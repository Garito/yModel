# yModel's change log
## 0.0.2
### Bug fixes
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