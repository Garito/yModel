from marshmallow import fields
from marshmallow.validate import ValidationError

from yModel import Schema, Tree, consumes, produces, can_crash, deprecate, OkSchema, ErrorSchema
from yModel.mongo import ObjectId, MongoSchema, MongoTree

class Minimal(Schema):
  name = fields.Str(required = True)

class MinimalBadTree(Minimal, Tree):
  pass

class MinimalTree(Minimal, Tree):
  path = fields.Str(required = True)
  slug = fields.Str(required = True)

class RealTree(MinimalTree):
  elements = fields.List(fields.Str)

  allowed_children = ["RealTree"]
  children_models = {"elements": "RealTree"}

class MinimalMongo(MongoSchema):
  _id = ObjectId(required = True)
  name = fields.Str(required = True)

class AnotherMongo(MinimalMongo):
  finished = fields.Bool()

class MinimalMongoTree(MinimalMongo, MongoTree):
  path = fields.Str(required = True)
  slug = fields.Str(required = True)

class RealMongoTree(MinimalMongoTree):
  members = fields.List(ObjectId)
  elements = fields.List(fields.Str)

  allowed_children = ["RealMongoTree", "User"]
  children_models = {"members": "User", "elements": "RealMongoTree"}

class User(MinimalMongoTree):
  pass

class NameOnlyRequestSchema(Schema):
  name = fields.Str(required = True)

class NameOnlyOkSchema(OkSchema):
  name = fields.Str(required = True)

class DecoratorsSchema(Schema):
  name = fields.Str(required = True)
  age = fields.Int()

  @can_crash(Exception, ErrorSchema, 404)
  @can_crash(ValidationError, ErrorSchema)
  @consumes(NameOnlyRequestSchema)
  @produces(NameOnlyOkSchema, as_ = "name")
  async def set_name(self, request, schema):
    if schema.__data__["name"] == "Exception":
      raise Exception("It can crash from a regular Exception")

    if schema.__data__["name"] == "MakeItCrash":
      raise ValidationError("Crash test")

    self.__data__["name"] = schema.__data__["name"]
    return self.__data__["name"]

  @deprecate()
  async def to_deprecate(self, request):
    return True
