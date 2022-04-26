import typing as t
from copy import deepcopy

from pymongo.errors import OperationFailure
from flask_mongodb.core.exceptions import CollectionException

from flask_mongodb.core.wrappers import MongoCollection
from flask_mongodb.models.fields import JsonField, ObjectIDField
from flask_mongodb.models.manager import CollectionManager


class BaseCollection:
    collection_name: str = None
    schemaless = False
    validation_level: str = 'strict'
    manager = CollectionManager
    _id = ObjectIDField()
    
    def __init__(self) -> None:
        self._fields = dict()
        self.__collection__: MongoCollection = None
        if not self.manager:
            raise ValueError('Missing collection manager')
        setattr(self, 'manager', self.manager(self))
        self.db = None
        
        for name in dir(self):
            if not name.startswith('_') or name == '_id':
                attr = getattr(self, name)
                if hasattr(attr, '_model_field'):
                    self._fields[name] = attr
    
    def __getattribute__(self, __name: str) -> t.Any:
        attr = super().__getattribute__(__name)
        if hasattr(attr, '_model_field'):
            try:
                return self._fields[__name].data
            except KeyError:
                return attr
        else:
            return attr
    
    def __setitem__(self, __name: str, __value: t.Any):
        field = self._fields.get(__name, None)
        if field is None:
            raise KeyError(f'CollectionModel does not field with name {__name}')
        if hasattr(__value, '_model_data'):
            raise ValueError('Cannot assign model field to this model field')
        field.data = __value
    
    def __getitem__(self, __name: str):
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
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result
    
    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result
    
    @property
    def fields(self) -> dict:
        return self._fields
    
    @property
    def pk(self):
        return self._id


class CollectionModel(BaseCollection):
    def __init__(self, **field_values):
        self._initial = {} if not field_values else field_values
        self._update = {}
        super(CollectionModel, self).__init__()
        
        if not self.collection_name:
            raise CollectionException('Need a collection name')

        # _id field must be excluded from the list of attrs not to include
        for attrib_name in [_ for _ in dir(self) if not _.startswith('_') or _ =='_id']:
            attrib = getattr(self, attrib_name)
            if hasattr(attrib, '_model_data'):
                self._fields[attrib_name] = attrib
        
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
    
    def data(self, as_str=False, exclude=()):
        _data = {}
        for name, field in self.fields.items():
            if name in exclude:
                # Go to next field
                continue
            if isinstance(field, JsonField):
                _data[name] = {}
                for prop_name, prop_field in field.properties.items():
                    _data[name][prop_name] = prop_field.data if not as_str else str(prop_field.data)
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
            if not field.allow_null:
                validators["$jsonSchema"]["properties"][name] = {
                    "bsonType": [field.bson_type]
                }
            else:
                validators["$jsonSchema"]["properties"][name] = {
                    "bsonType": [field.bson_type, "null"]
                }

            if max_length := getattr(field, 'max_length', None):
                validators["$jsonSchema"]["properties"][name].update({'maxLength': max_length})

            if min_length := getattr(field, 'min_length', None):
                validators["$jsonSchema"]["properties"][name].update({'minLength': min_length})

            if isinstance(field, JsonField):
                validators['$jsonSchema']["properties"][name]["required"] = []
                
                for prop_name, prop_field in field.properties.items():
                    if isinstance(prop_field, JsonField):
                        raise CollectionException('Document can only have two levels of objects')
                    
                    validators["$jsonSchema"]["properties"][name]["properties"] = {prop_name: {}}
                    if prop_field.required:
                        validators['$jsonSchema']["properties"][name]["required"].append(prop_name)
                    
                    if not prop_field.allow_null:
                        validators["$jsonSchema"]["properties"][name]["properties"][prop_name] = {
                            "bsonType": [prop_field.bson_type]
                        }
                    else:
                        validators["$jsonSchema"]["properties"][name]["properties"][prop_name] = {
                            "bson_type": [prop_field.bson_type, "null"]
                        }
                    
                    if max_length := getattr(prop_field, 'max_length', None):
                        validators["$jsonSchema"]["properties"][name]["properties"][prop_name].update({'maxLength': max_length})

                    if min_length := getattr(prop_field, 'min_length', None):
                        validators["$jsonSchema"]["properties"][name]["properties"][prop_name].update({'minLength': min_length})
            
                if not validators['$jsonSchema']['properties'][name]['required']:
                    validators['$jsonSchema']['properties'][name].pop('required')  # If required field empty, remove
                
        if not validators['$jsonSchema'].get('required'):
            validators['$jsonSchema'].pop('required')  # Remove required field if empty list
        return validators if validators['$jsonSchema']['properties'] else {}

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
    
    def save(self, update_data: dict = None, force=False, update_type='$set', upsert=False, **other_options):
        if update_data:
            self._update.update(**update_data)
        if not self._update:
            raise Exception('Cannot save data that has not been modified')
        update = {update_type: self._update}
        self.manager.update_one(query={'_id':self._id}, update=update, upsert=upsert, 
                                bypass_document_validation=force, **other_options)
