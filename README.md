# yModel
Schema is a [Marshmallow](https://marshmallow.readthedocs.io) subclass that saves the data and errors to private members (that you can access by using self.get_data() and self.get_errors())

The point is to not need a data class since, in an API context, all we need is json in json out

It highly uses decorators to avoid (because is automatic) the need of validation and post processing the response

Tree is the tree version with materialized paths and order in a object member (if needed)

MongoSchema and yMongoTree are the MongoDB versions for CRUD plain schemas and tree structures

It is part of the yRest framework (which includes [ySanic](https://github.com/Garito/ySanic) and [yAuth](https://github.com/Garito/yAuth) by the moment and yOpenSanic in the future)

## Example
```python
class Person(Schema):
  name = fields.Str(required = True)
  age = fields.Int()

  @can_crash(Exception, ErrorSchema, 404)
  @can_crash(ValidationError, ErrorSchema)
  @consumes(NameOnlyRequestSchema)
  @produces(NameOnlyOkSchema, as_ = "name")
  async def set_name(self, request, schema):
    if schema.get_data()["name"] == "Exception":
      raise Exception("It can crash from a regular Exception")

    if schema.get_data()["name"] == "MakeItCrash":
      raise ValidationError("Crash test")

    self.get_data()["name"] = schema.get_data()["name"]
    return self.get_data["name"]

  @deprecate()
  async def to_deprecate(self, request):
    return True
```

As you can see, the first part of the class is a regular marshmallow class with fields declaration

The interesting part is the ```set_name``` and ```to_deprecate``` members full of decorators

```set_name``` consumes a ```NameOnlyRequestSchema``` (which is another yModel use for input validation) that will be filled with the request.json (by default)

With this decorator you will recieve an extra ```*args``` item with the model already validated

Then it produces a ```NameOnlyOkSchema``` with the return value from the function. So in this case will be something like
```json
{
  "ok": true,
  "result": "the name of the person"
}
```
can_crash automates the error processing by returning a response like
```json
{
  "ok": false,
  "message": "the raised error"
}
```
in the example two exception has been defined:

If the name passed is "Exception" will raise a regular python Exception which will be captured by the first ```can_crash``` returning and ```ErrorSchema``` and a 404 status

```json
{
  "ok": false,
  "message": "It can crash from a regular Exception"
}
```

If the name passed is "MakeItCrash" it will be captured by the second ```can_crash``` and will return an ```ErrorSchema``` too but with the status 400

```json
{
  "ok": false,
  "message": "Crash test"
}
```

yModel defines some basic schemas for returning ok ```OkSchema``` and not ok ```ErrorSchema``` that you can subclass with your own needs (or even use a schema build by you from scratch. It only needs to be a subclass of yModel)

The ```deprecated``` decorator will be mostly useful with the yOpenSanic to mark an API endpoint as deprecated

This decorators will help later for introspection since the tree structures are tricky to instrospect

## Installation
```pip install yModel```

## Tree structures
Add a ```path``` and ```name``` fields to build the materialized path or add a ```@pre_load``` function if you need a different source for the slug (it's using [python-slugify](https://github.com/un33k/python-slugify) but you can use any one else if you add your own ```@pre_load``` function)

Check out the tests for examples

## MongoDB
Use this class as a guide to create you own backend need (will be nice if you pull request it to this project if the backend is an open sourced one)

## Help
Feel free to help if you think something is weird or incomplete by submiting a pull request

I've spend an indecent amount of time dealing with tree structures to know what's essential for that matter but will be no surprise if you have a nice idea to improve this code (at the end of the day I bet you are a smart person)

### What is already needed
- [] Elasticsearch module
- [] Redis module
- [] More testing
- [] Continous integration
- [] Better help & documentation
 
### I'm not a technical person but still want to help
You can tip the project with cryptos too:

BTC: 1GtKxwZGR65ar9V8xafxhMiniZyqXej2GC

ETH: 0x01bd478b8C07633D2f4E58AC553f72CE4E590d56

LTC: LYUzrFX6ck5uMhw5VqcD9piQHnX7oeSLdh

XMR: 49stcvbfjEkWLjb6mdG21zMJ3uRrLmN3bazGQ8cHjjsVHYYyY61N6P7emCXhpsvB2Vc8Uuz2FA1Qk6hkE8e4ADmJQQ64eyT

ADA: DdzFFzCqrhsoUF5UjGGAYUayV5uNCJZ17PJn9V8X9MTQ26m2wDVycme42gufKufPNWMazfJLg8RKHpc1iFvn6j8BTJjaozGtLPzCDx5t

NEM: NDGYO6X3NTD6CX3V7MCCYKQPBIOYGZRXEKDLCDW2
