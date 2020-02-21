from schema import Schema, Use, And, Or, Optional, Hook
import json
import arrow

# Doesn't need special functionality, just needs to be notable
# as a separate type
class ReadOnly(Hook): pass

class DayliteData:
    __schema__ = None
    __client__ = None
    def __init__(self, schema, data, client=None):
        data = schema.validate(data)
        vars(self).update(data)
        self.__schema__ = schema
        self.__client__ = client
    
    def from_json(self, data):
        data = self.__schema__.validate(json.loads(data))
        vars(self).update(data)
    
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if self.__schema__ is not None:
            self.__schema__.validate(vars(self))
            
    def __getattr__(self, name):
        val = super().__getattr__(name)
        if type(val) == Reference:
            val.set_client(self.__client__)
        return val
        
    def has_key(self, name):
        
        for key in self.__schema__.keys():
            if type(key) != str:
                # Implementation detail _ness_ from 
                # Schema.
                # TODO: Make this more robust?
                key = key.schema
            if key == name:
                return True
        return False
    
class Reference:
    """
    Provides a mechanism for background loading of objects,
    so that we can fetch more details, as and when needed
    This is expected to promote/replace/etc itself with a
    DayliteData object once it has been accessed
    """
    _ref            = None
    _daylitedata    = None
    _client         = None
    _schema         = None
    def __init__(self, schema, ref):
        self._schema = schema
        self._ref = ref
        
    def _set_client(self, client):
        
        self._client = client
    
    def __setattr__(self, name, value):
        if name.startswith('_') or name in ('validate',):
            super().__setattr__(name, value)
        else:
            self._daylitedata.__setattr__(name, value)
        
    def __getattr__(self, name):
        # Special case getting attributes that are on this class
        # instead of passing them down to the wrapped class
        if name.startswith('_') or name in ('validate',):
            return super().__getattr__(name)
        
        if self._daylitedata is None:
            # Special case the "self" element for scenarios
            # where the underlying ID is already known and we don't
            # have to go fetch it
            if name == "self":
                return self._ref
            # okay, we need to fetch the data for this object
            self._daylitedata = self._client.fetch(self.schema, self.__ref__)
        
        return self._daylitedata.__getattr__(name)
        
    def validate(self):
        """Needs to support the schema validation contract"""
        return True # it's all valid! for now!
    

Date = Schema({
    "day": And(int, lambda x: x > 0),
    "month": And(int, lambda x: x > 0),
    Optional("year"): And(int, lambda x: x > 1900)
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

Thin_Contact = Schema({
    "self":                         And(str, len),
    Optional("first_name"):         And(str, len),
    Optional("middle_name"):        And(str, len),
    Optional("last_name"):          And(str, len),
},
ignore_extra_keys=True)

Contact = Schema(
    {
    ReadOnly("self"):               And(str, len),
    Optional("prefix"):             str,
    Optional("first_name"):         And(str, len),
    Optional("middle_name"):        str,
    Optional("last_name"):          And(str, len),
    Optional("suffix"):             str,
    ReadOnly("full_name"):                    str,
    Optional("alias"):              str,
    Optional("nickname"):           str,
    Optional("image"):              str,
    Optional("category"):           str,
    Optional("keywords"):           Schema([str]),
    
    Optional("birthday"):           Date,
    Optional("anniversary"):        Date,
    
    Optional("phone_numbers"):      Schema([Phone_Numbers]),
    Optional("emails"):             Schema([Emails]),
    Optional("social_profiles"):    Schema([Social_Profiles]),
    Optional("urls"):               Schema([Urls]),
    Optional("addresses"):          Schema([Address]),
    Optional("companies"):          Schema([Company_Roles]),
    Optional("opportunities"):      Schema([Opportunity_Roles]),
    Optional("details"):            str,
    
    # These things are always here
    
    # TODO: Make these a reference types instead
    ReadOnly("owner"):              And(str, len),
    ReadOnly("creator"):            And(str, len),
    # Yay dates
    ReadOnly("create_date"):        Use(arrow.get),
    ReadOnly("modify_date"):        Use(arrow.get)
},
name="Contact",
ignore_extra_keys=True)