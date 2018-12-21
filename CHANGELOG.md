# yModel's change log
## 0.0.2
### Bug fixes
#### Base model
Consume wasn't respecting the many attribute when loading the input data

Corrected two test to reflect the change of the raised error

Automatic slugification as a pre_load
By default slugifies the name but you can define a ```slugable``` member with the name of the field you want to use as slug or a function that recieves the whole data dict and returns the slug

You can now exclude fields before to_json and to_plain_dict
It is useful for not send the user's password field for instance

OkResult that returns a structure like {"ok": True, result: <your result>}
OkListResult that returns a list @ result and
OkDictResult that returns a dict instead
are now available

The decorator ```consumes``` now accept two new params: getter and description
getter is a function that is use to allow to pass a function to extract the information
Useful to extract headers data or other data in particular places of the request
description is used to describe the consumer for documentation/openapi purposes
It raises a better exception if the model can't validate the data

Better detection of request in the decorators

The decorator ```produces```now accept renderer and description in a similar manner than ```consumes```
Since it is an output decorator, it has renderer instead of getter, to allow to customize the way that it renders the produced result
It is possible to use the name of the model instead of the model itself in the declaration. This allows to use a model not yet declared or declared anywhere else (example Auth that belongs to yAuth package but allows to personalize visible info for the user)
Better validation flow in the same way that with ```consumes```

```can_crash``` now accept the same new arguments that ```produces``` (renderer and description) for the same reason

```deprecated``` want to know the reason for the deprecation

#### MongoDB model
DateTime is not longer needed since the original field has everything we need
The update now returns the model of the modifications validated