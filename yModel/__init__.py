from json import loads, dumps
from functools import wraps

from marshmallow import Schema as mSchema, pre_load, fields
from marshmallow.validate import ValidationError

from slugify import slugify

class Schema(mSchema):
  class Meta:
    ordered = True

  def __init__(self, table = None, **kwargs):
    super().__init__(**kwargs)
    self.table = table
    self.__data__ = [] if "many" in kwargs and kwargs["many"] else {}

  def __getattr__(self, name):
    if name in self.__data__:
      return self.__data__[name]

    raise AttributeError("{} object has no attribute {}".format(self.__class__.__name__, name))

  @pre_load
  def slug_preload(self, data):
    if "slug" in self.fields.keys() and ("slug" not in data or not data["slug"]):
      slugable = self.slugable if hasattr(self, "slugable") else "name"
      data["slug"] = slugify(data.get(slugable, "")) if isinstance(slugable, str) else slugable(data)

    return data

  def load(self, data, many = None, partial = None):
    res = super().load(data, many = many, partial = partial)
    if hasattr(res, "data") and res.data:
      self.__data__ = list(res.data) if many else dict(res.data)
    if hasattr(res, "errors") and res.errors:
      self.__errors__ = dict(res.errors)

  def get_data(self):
    return self.__data__

  def get_errors(self):
    return getattr(self, "__errors__", None)

  def to_json(self, exclude = None):
    data = self.get_data().copy()
    if exclude is None and hasattr(self, "exclusions"):
      exclude = self.exclusions
    if exclude:
      for element in data if isinstance(data, list) else [data]:
        for member in exclude:
          if member in element:
            del element[member]

    return dumps(data, cls = self.encoder) if hasattr(self, "encoder") else dumps(data)

  def to_plain_dict(self, exclude = None):
    return loads(self.to_json(exclude))

class Tree():
  def children_of_type(self, type_):
    return [child for child, model in (self.children_models or {}).items() if model == type_]

  def get_url(self):
    if self.path == "":
      return "/"
    else:
      return "/{}".format(self.slug) if self.path == "/" else "{}/{}".format(self.path, self.slug)

class OkSchema(Schema):
  ok = fields.Bool(missing = True)

class ErrorSchema(Schema):
  ok = fields.Bool(missing = False)
  message = fields.Str(required = True)
  code = fields.Int(required = True)

class OkResult(OkSchema):
  result = fields.Str(required = True)

class OkDictResult(OkSchema):
  result = fields.Dict(required = True)

class OkListResult(OkSchema):
  result = fields.List(fields.Dict, required = True)

def consumes(model, many = None, from_ = "json", getter = None, description = None):
  def decorator(func):
    if not hasattr(func, "__decorators__"):
      func.__decorators__ = {}
    func.__decorators__["consumes"] = {"model": model, "many": many, "from": from_, "getter": getter, "description": description}

    @wraps(func)
    async def decorated(*args, **kwargs):
      request = None
      for arg in args:
        if hasattr(arg, "app") and hasattr(arg.app, "models"):
          request = arg
          break

      if request is None:
        raise InvalidRoute(func.__name__)

      modelObj = (getattr(request.app.models, model) if isinstance(model, str) else model)(many = many)
      payload = getter(getattr(request, from_)) if getter else getattr(request, from_)
      modelObj.load(payload, many = many)
      errors = modelObj.get_errors()
      if errors:
        raise ValidationError(errors)
      else:
        listargs = list(args)
        listargs.append(modelObj)
        args = tuple(listargs)

      result = await func(*args, **kwargs)
      return result

    return decorated
  return decorator

def produces(model, many = None, as_ = None, renderer = None, description = None):
  def decorator(func):
    if not hasattr(func, "__decorators__"):
      func.__decorators__ = {}
    func.__decorators__["produces"] = {"model": model, "many": many, "as_": as_, "renderer": renderer, "description": description}

    @wraps(func)
    async def decorated(*args, **kwargs):
      request = None
      for arg in args:
        if hasattr(arg, "app") and hasattr(arg.app, "models"):
          request = arg
          break

      if request is None:
        raise InvalidRoute(func.__name__)

      result = await func(*args, **kwargs)

      modelObj = (getattr(request.app.models, model) if isinstance(model, str) else model)(many = many)
      if as_ is not None:
        data = {}
        data[as_] = result
        modelObj.load(data, many = many)
        errors = modelObj.get_errors()
        if errors or getattr(modelObj, as_) != result:
          raise ValidationError("{} is not producing a valid {}: {}".format(func.__name__, model, data))
      elif not isinstance(result, modelObj.__class__):
        if result is None:
          result = {}
        modelObj.load(result, many = many)
        errors = modelObj.get_errors()
        if errors:
          raise ValidationError("{} is not producing a valid {}: {} -> {}".format(func.__name__, model, result, errors))
      else:
        modelObj = result

      return modelObj if renderer is None else renderer(modelObj)

    return decorated
  return decorator

def can_crash(exc, model = ErrorSchema, getter = "__str__", code = 400, renderer = None, description = None):
  def decorator(func):
    if not hasattr(func, "__decorators__"):
      func.__decorators__ = {}
    if "can_crash" not in func.__decorators__:
      func.__decorators__["can_crash"] = {}

    func.__decorators__["can_crash"][exc.__name__] = {"model": model, "exc": exc, "code": code, "renderer": renderer, "description": description}

    @wraps(func)
    async def decorated(*args, **kwargs):
      try:
        result = await func(*args, **kwargs)
        return result
      except exc as e:
        modelObj = model()
        getterMember = getattr(e, getter)
        message = getterMember() if callable(getterMember) else getterMember      
        modelObj.load({"message": message, "code": code})

        return modelObj if renderer is None else renderer(modelObj.to_plain_dict())

    return decorated
  return decorator

def deprecate(reason):
  def decorator(func):
    if not hasattr(func, "__decorators__"):
      func.__decorators__ = {}
    func.__decorators__["deprecate"] = reason

    @wraps(func)
    async def decorated(*args, **kwargs):
      result = await func(*args, **kwargs)
      return result

    return decorated
  return decorator
