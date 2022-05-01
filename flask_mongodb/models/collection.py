import typing as t
from copy import deepcopy

from pymongo.errors import OperationFailure
from flask_mongodb.core.exceptions import CollectionException

from flask_mongodb.core.wrappers import MongoCollection
from flask_mongodb.models.fields import EmbeddedDocumentField, EnumField, Field, ObjectIdField, ReferenceIdField
from flask_mongodb.models.manager import CollectionManager


class BaseCollection:
    collection_name: str = None
    schemaless = False
    validation_level: str = 'strict'
    manager = CollectionManager
    _id = ObjectIdField()
    
    def __init__(self) -> None:
        self._fields = dict()
        self.__collection__: MongoCollection = None
        if not self.manager:
            raise ValueError('Missing collection manager')
        setattr(self, 'manager', self.manager(self))
        setattr(self, '_id', self._id)
        self._fields['_id'] = self._id
        self.db = None
        
        for name in dir(self):
            if not name.startswith('_'):
                attr = getattr(self, name)
                if hasattr(attr, '_model_field'):
                    self._fields[name] = attr

    def __setitem__(self, __name: str, __value: t.Any):
        # Dict style assignment
        field = self._fields.get(__name, None)
        if field is None:
            raise KeyError(f'CollectionModel does not field with name {__name}')
        if hasattr(__value, '_model_data'):
            raise ValueError('Cannot assign model field to this model field')
        field.data = __value
    
    def __getitem__(self, __name: str):
        # Dict style getting
        field = self._fields.get(__name, None)
        if field is None:
            raise KeyError(f'Not a valid field with name {__name}')
        return field.data
    
    def __str__(self):
        return self.collection_name
    
    def __iter__(self):
        return iter(self._fields.values())
    
    def __repr__(self):
        return f"{self.__class__}.{self.collection_name}"
    
    def __contains__(self, __name: str):
        return __name in self._fields
    
    def __copy__(self):
        cls = self.__class__
        obj = cls.__new__(cls)
        obj.__dict__.update(self.__dict__)
        return obj
    
    def __deepcopy__(self, memo):
        cls = self.__class__
        obj = cls.__new__(cls)
        memo[id(self)] = obj
        for k, v in self.__dict__.items():
            setattr(obj, k, deepcopy(v, memo))
        return obj
    
    @property
    def fields(self) -> dict:
        return self._fields
    
    @property
    def pk(self):
        return self._id.data


class CollectionModel(BaseCollection):
    def __init__(self, **field_values):
        self._initial = {} if not field_values else field_values
        self._update = {}
        super(CollectionModel, self).__init__()
        
        if not self.collection_name:
            raise CollectionException('Need a collection name')
        
        for name, field in self._fields.items():
            # Make fields accessible by the dot convension and obscure class attribute
            # names
            setattr(self, name, field)
        
        if self._initial:
            "Assign the respective field their data, even if the field does not exist"
            for name, data in self._initial.items():
                field = self._fields.get(name, None)
                if field is None:
                    # If field name not part of collection, ignore it
                    continue
                field.data = data
        
        self.schema_validators = None
    
    def __setitem__(self, __name: str, __value: t.Any):
        field = self._fields.get(__name, None)
        if field is None:
            raise KeyError(f'CollectionModel does not field with name {__name}')
        if hasattr(__value, '_model_data'):
            raise ValueError('Cannot assign model field to this model field')
        field.data = __value
        
        if __name not in self._update:
            self._update[__name] = __value
        else:
            if self._update[__name] != __value:
                self._update[__name] = __value
    
    @property
    def collection(self) -> MongoCollection:
        return self.__collection__
    
    def data(self, as_str=False, exclude=(), include_reference=True, include_all_references=False):
        _data = {}
        for name, field in self.fields.items():
            if name in exclude:
                # Go to next field
                continue
            if isinstance(field, EmbeddedDocumentField):
                _data[name] = {}
                for prop_name, prop_field in field.properties.items():
                    _data[name][prop_name] = prop_field.data if not as_str else str(prop_field.data)
            elif isinstance(field, ReferenceIdField) and include_reference:
                ref = field.reference
                if ref is None:
                    # CONSIDER: If best option is to raise and error
                    _data[name] = ref
                    continue
                _data[name] = field.reference.data(as_str, exclude, 
                                                    include_reference=include_all_references,
                                                    include_all_references=include_all_references)
            else:
                _data[name] = field.data if not as_str else str(field.data)
        return _data

    def __define_validators__(self):
        validators = {
            '$jsonSchema': {
                "bsonType": "object",
                "required": [],
                "properties": {}
            }
        }
        for name, field in self.fields.items():
            if field.required:
                validators["$jsonSchema"]["required"].append(name)
            
            # Defining field BSON types
            if field.bson_type is not None:
                validators['$jsonSchema']["properties"][name] = {
                    "bsonType": deepcopy(field.bson_type)
                }

                # If has BSON Type, check if null is allowed and add it
                if field.allow_null:
                    validators["$jsonSchema"]["properties"][name]["bsonType"].append('null')
            
            if isinstance(field, EnumField):
                if field.bson_type is not None:
                    # TODO: Exception needed here
                    raise Exception('The enum of the EnumField will establish the valid types')
                
                enum = {'enum': field.enum}
                if field.allow_null:
                    enum['enum'].append('null')
                validators['$jsonSchema']['properties'][name] = enum

            # Add max_length if it has it
            if max_length := getattr(field, 'max_length', None):
                validators["$jsonSchema"]["properties"][name].update({'maxLength': max_length})

            # Add min_length if it has it
            if min_length := getattr(field, 'min_length', None):
                validators["$jsonSchema"]["properties"][name].update({'minLength': min_length})
            
            if field.description:
                validators["$jsonSchema"]["properties"][name].update({'description': field.description})

            if isinstance(field, EmbeddedDocumentField):
                sub_validators = self._embedded_document_validators(field)
                validators['$jsonSchema']['properties'][name].update(sub_validators)
        
        if not validators['$jsonSchema'].get('required'):
            validators['$jsonSchema'].pop('required')  # Remove required field if empty list
        return validators if validators['$jsonSchema']['properties'] else {}
    
    def _embedded_document_validators(self, field: Field):
        sub_validators = {
            "bsonType": [],
            "required": [],
            "properties": {}
        }
        
        sub_validators['bsonType'] = field.bson_type
        if field.allow_null:
            sub_validators['bsonType'].append('null')
        
        for prop_name, prop_field in field.properties.items():
            if prop_field.required:
                sub_validators["required"].append(prop_name)
            
            # Defining field BSON types
            if prop_field.bson_type is not None:
                sub_validators["properties"][prop_name] = {
                    "bsonType": deepcopy(prop_field.bson_type)
                }

                # If has BSON Type, check if null is allowed and add it
                if prop_field.allow_null:
                    sub_validators['properties'][prop_name]["bsonType"].append('null')
            
            if max_length := getattr(prop_field, 'max_length', None):
                sub_validators["properties"][prop_name].update({'maxLength': max_length})

            if min_length := getattr(prop_field, 'min_length', None):
                sub_validators["properties"][prop_name].update({'minLength': min_length})
            
            if isinstance(prop_field, EmbeddedDocumentField):
                # Support for Embedded documents in embedded documents
                sub_sub_validators = self._embedded_document_validators(prop_field)
                sub_validators['properties'][prop_name].update(sub_sub_validators)
    
        if not sub_validators['required']:
            sub_validators.pop('required', None)  # If required field empty, remove it
        
        return sub_validators

    def __assign_data_to_fields__(self):
        for name, field in self.fields.items():
            value = self._initial.get(name)
            if value is None:
                # Ignore fields that do not exist
                continue
            field.data = value
    
    def connect(self, database):
        self.db = database
        self.schema_validators = self.__define_validators__() if not self.schemaless else None
        try:
            # Will first try to create a collection
            self.__collection__ = MongoCollection(database, self.collection_name, 
                                                  create=True,
                                                  validator=self.schema_validators,
                                                  validationLevel=self.validation_level if not self.schemaless else None)
        except OperationFailure:
            # If collection exists, use that collection
            self.__collection__ = MongoCollection(database, self.collection_name)
    
    def set_model_data(self, data: dict):
        self._initial = data
        self.__assign_data_to_fields__()
