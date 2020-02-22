from schema import Schema, Use, And, Or, Optional, Hook
import json
import arrow
from pathlib import PurePath
import collections

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
    
    @classmethod
    def _server(cls, schema, data: dict, client=None):
        # Data is already a dict, since the it's coming from the 
        # server fetch stage instead of expecting to be parsed
        # from json outrselves
        
        self = cls(schema, data, client)
        server_data = Server_Data.validate(data)
        vars(self).update(server_data)
        return self
        
    def _set_client(self, client):
        self.__client__ = client
    
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if self.__schema__ is not None:
            self.__schema__.validate(vars(self))
    
    # def __getattr__(self, name):
    #     return super().__getattr__(name)
    
    def __getattribute__(self, name):
        # print("DayliteData: getting attr {}".format(name))
        val = super().__getattribute__(name)
        # val = self.__getattr__(name)
        if type(val) in (DayliteData, DayliteDataList, Reference):
            val._set_client(self.__client__)
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
    
class DayliteDataList(collections.UserList):
    
    _client = None
    _schema = None
    
    def __init__(self, data):
        self.data = data
        
    def _schema(self, schema):
        self._schema = schema
        
    def _set_client(self, client):
        # print("setting client")
        self._client = client
        
    def __getitem__(self, idx):
        # print("Getting idx {}".format(idx))
        item = self.data.__getitem__(idx)
        if type(idx) == slice:
            # print("is a slice")
            d = DayliteDataList(item)
            d._schema = schema
            d._client = self._client
            return d
            
        if type(item) not in (DayliteData, Reference):
            # print("Isn't a data object or a reference, promoting")
            item = DayliteData(self._schema, item)
            self[idx] = item
        
        # print("Trying to set client")
        if self._client is not None:
            item._set_client(self._client)
        # print("Our client isn't set, wtf")
        
        return item

def list_factory(schema):
    def _factory(ref):
        if type(ref) == DayliteDataList:
            return ref
        d = DayliteDataList(ref)
        d._schema = schema
        return d
    return _factory
    

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
    def __init__(self, ref):
        # self._schema = schema
        self._ref = ref
        reftype = str(PurePath(ref).parents[0])
        self._schema = reference_map[reftype]
        
    @classmethod
    def factory(cls, ref):
        if type(ref) == cls:
            return ref
        return cls(ref)
        
    def __repr__(self):
        return "Reference('{}')".format(self._ref)
        
    def _set_client(self, client):
        
        self._client = client
    
    def __setattr__(self, name, value):
        if name.startswith('_') or name in ('validate',):
            # print("setting {} to {} via super".format(name, value))
            super().__setattr__(name, value)
        else:
            set(self._daylitedata, name, value)
            # self._daylitedata.__setattr__(name, value)
        
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
            # print("Generating wrapped object to fetch {}".format(name))
            # print("Using reference {}".format(self._ref))
            self._daylitedata = self._client.fetch(self._schema, self._ref)
        
        # return self._daylitedata.get(name)
        # print("Getting {} from wrapped daylite object".format(name))
        # print(dir(self._daylitedata))
        return getattr(self._daylitedata, name)
        
    def validate(self):
        """Needs to support the schema validation contract"""
        return self._schema is not None
    

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

Company_Roles = Schema(
{
    "company": Use(Reference.factory),
    Optional("role"): And(str, len),
    Optional("title"): And(str, len),
    Optional("department"): And(str, len),
    Optional("default"): bool
},
ignore_extra_keys=True)

Contact_Roles = Schema({
    Optional("title"): str,
    Optional("department"): str,
    Optional("role"): str,
    ReadOnly("contact"): Use(Reference.factory)
},
ignore_extra_keys=True)

Opportunity_Roles = Schema({
    "opportunity": Use(Reference.factory),
    "title": str,
    "role": str,
})

Project_Roles = Schema({
    "project": Use(Reference.factory),
    "title": str,
    "role": str
})

Tasks_Internal = Schema({
    "task": Use(Reference.factory)
})

Appointments_Internal = Schema({
    "appointment": Use(Reference.factory)
})

Groups_Internal = Schema({
    "group": Use(Reference.factory)
})


# TODO: Make this proper reference-url-like handling
Url = Schema(str)

Thin_Contact = Schema({
    "self":                         And(str, len),
    Optional("first_name"):         And(str, len),
    Optional("middle_name"):        And(str, len),
    Optional("last_name"):          And(str, len),
},
ignore_extra_keys=True)

Contact = Schema(
    {
    Optional("prefix"):             str,
    Optional("first_name"):         And(str, len),
    Optional("middle_name"):        str,
    Optional("last_name"):          And(str, len),
    Optional("suffix"):             str,
    ReadOnly("full_name"):          str,
    Optional("alias"):              str,
    Optional("nickname"):           str,
    Optional("image"):              str,
    Optional("category"):           str,
    Optional("keywords"):           Schema([str]),
    
    Optional("birthday"):           Date,
    Optional("anniversary"):        Date,
    
    # These are lists of internal lists of data, not remote objects
    
    Optional("phone_numbers"):      Schema([Phone_Numbers]),
    Optional("emails"):             Schema([Emails]),
    Optional("social_profiles"):    Schema([Social_Profiles]),
    Optional("urls"):               Schema([Urls]),
    Optional("addresses"):          Schema([Address]),

    # These are lists of references to other objects
    
    Optional("companies"):          Use( list_factory( Company_Roles ) ),
    Optional("opportunities"):      Use( list_factory( Opportunity_Roles ) ),
    
    # Back to generic details
    
    Optional("details"):            str,
    
    # This is a reference to a User
    Optional("owner"):              Use(Reference.factory),
},
name="Contact",
ignore_extra_keys=True)

Company = Schema({
    # This is technically a reference however it's nonsense to have a 
    # reference object to ourselves
    Optional("name"):               And(str, len),
    Optional("image"):              And(str, len), # TODO: How is this even?
    Optional("category"):           And(str, len),
    Optional("keywords"):           Schema([str]),
    Optional("type"):               And(str, len),
    Optional("industry"):           And(str, len),
    Optional("region"):             And(str, len),
    Optional("emails"):             Schema([Emails]),
    Optional("urls"):               Schema([Urls]),
    Optional("social_profiles"):    Schema([Social_Profiles]),
    Optional("phone_numbers"):      Schema([Phone_Numbers]),
    Optional("addresses"):          Schema([Address]),
    
    Optional("contacts"):           Use( list_factory( Contact_Roles ) ),
    Optional("opportunities"):      Use( list_factory( Opportunity_Roles ) ),
    
    Optional("details"):            And(str, len),
    
    # This is a reference to a User
    Optional("owner"):              Use(Reference.factory)
},
ignore_extra_keys=True)


User = Schema({
    ReadOnly("login"):              And(str, len),
    ReadOnly("contact"):            Use(Reference.factory),
    Optional("hex_colour"):         And(str, len)
},
ignore_extra_keys=True)


# This is only used by the validator when the data is coming from
# the server, instead of when it's coming from a developer creating a new
# object from scratch, pre-save-to-server
# This is broken out so that creating a new object doesn't
# create sad times as you walk through creating and modifying it

Server_Data = Schema({
    ReadOnly("self"):               And(str, len, Url),
    ReadOnly("create_date"):        Use(arrow.get),
    ReadOnly("modify_date"):        Use(arrow.get),
},
ignore_extra_keys=True)

reference_map = {
    "/v1/contacts":                 Contact,
    "/v1/companies":                Company,
    "/v1/users":                    User,
    "/v1/opportunities":            Opportunity,
}