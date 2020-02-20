from schema import Schema, Use, And, Or, Optional, Hook
import json
import arrow

# Doesn't need special functionality, just needs to be notable
# as a separate type
class ReadOnly(Hook): pass

Date = Schema({
    "day": And(int, lambda x: x > 0),
    "month": And(int, lambda x: x > 0),
    Optional("year"): And(int, lambda x: x > 0)
})

Emails = Schema({
    "label": And(str, len),
    "address": And(str, len),
    Optional("note"): str
})

Social_Profiles = Schema({
    "label": str,
    "service": str,
    "username": str
})

Urls = Schema({
    "label": str,
    "url": str,
    Optional("note"): str
})

Phone_Numbers = Schema({
    "label": str,
    "format": str,
    "number": str,
    Optional("note"): str
})

Address = Schema({
    "label": str,
    "street": str,
    "city": str,
    Optional("state"): str,
    "postal_code": str,
    "country": str,
    Optional("note"): str
})

Company_Roles = Schema({
    "company": str, # TODO: This is a reference
    "role": str,
    "title": str,
    "department": str,
})

Opportunity_Roles = Schema({
    "opportunity": str, # TODO: This is a reference
    "title": str,
    "role": str,
})

Project_Roles = Schema({
    "project": str, # TODO: This is a reference
    "title": str,
    "role": str
})

Tasks_Internal = Schema({
    "task": str # TODO: This is a reference
})

Appointments_Internal = Schema({
    "appointment": str # TODO This is a reference
})

Groups_Internal = Schema({
    "group": str # TODO this is a reference
})

Contact = Schema(
    {
    "self":                         And(str, len),
    Optional("prefix"):             str,
    "first_name":                   And(str, len),
    Optional("middle_name"):        str,
    "last_name":                    And(str, len),
    Optional("suffix"):             str,
    "full_name":                    str,
    Optional("alias"):              str,
    Optional("nickname"):           str,
    Optional("image"):              str,
    Optional("category"):           str,
    Optional("keywords"):           Schema([str]),
    
    Optional("birthday"):           Date,
    Optional("anniversary"):        Date,
    
    Optional("phone_numbers"):      Schema([str]),
    Optional("emails"):             Schema([str]),
    Optional("social_profiles"):    Schema([str]),
    Optional("urls"):               Schema([str]),
    Optional("addresses"):          Schema([Address]),
    Optional("companies"):          Schema([str]),
    Optional("opportunities"):      Schema([Opportunity]),
    Optional("details"):            str,
    
    # These things are always here
    
    # TODO: Make this a reference type instead
    "owner":                        And(str, len),
    "creator":                      And(str, len),
    "create_date":                  arrow.get,
    "modify_date":                  arrow.get
},
name="Contact",
ignore_extra_keys=True)

data = {
    "self":"asdf",
    "first_name":"aurynn",
    "last_name":"shaw",
    "owner": "1", 
    "creator": "1", 
    "full_name":"aurynn shaw", 
    "create_date": 1,
    "modify_date": 1, 
    "keywords":["one","two","three"],
    "birthday": {"day": 1, "month": 3}
}

dj = json.dumps(data)

class DayliteData:
    __schema__ = None
    def __init__(self, schema, data):
        data = schema.validate(data)
        vars(self).update(data)
        self.__schema__ = schema
    
    def from_json(self, data):
        data = self.__schema__.validate(json.loads(data))
        vars(self).update(data)
    
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if self.__schema__ is not None:
            self.__schema__.validate(vars(self))