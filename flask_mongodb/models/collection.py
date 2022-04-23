import typing as t

from pymongo.errors import OperationFailure
from flask_mongodb.core.exceptions import CollectionException

from flask_mongodb.core.wrappers import MongoCollection
from flask_mongodb.models.fields import Field, JsonField, ObjectIDField


class BaseCollection(object):
    collection_name: str = None
    validation_level: str = 'strict'
    _id = ObjectIDField()
    
    def __init__(self) -> None:
        self._fields = dict()
        self.__collection__: MongoCollection = None
        
        for name in dir(self):
            if not name.startswith('_') or name == '_id':
                attr = getattr(self, name)
                if hasattr(attr, '_model_field'):
                    self._fields[name] = attr
    
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
    
    @property
    def fields(self) -> dict:
        return self._fields
    
    @property
    def pk(self):
        return self._id.data


class CollectionModel(BaseCollection):
    def __init__(self, database):
        self.__data__ = {}
        super(CollectionModel, self).__init__()
        
        if not self.collection_name:
            raise CollectionException('Need a collection name')

        # _id field must be excluded from the list of attrs not to include
        for attrib_name in [_ for _ in dir(self) if not _.startswith('_') or _ =='_id']:
            attrib = getattr(self, attrib_name)
            if issubclass(type(attrib), Field):
                self._fields[attrib_name] = attrib
        
        self.validators = self.__define_validators__()
        try:
            # Will first try to create a collection
            self.__collection__ = MongoCollection(database, self.collection_name, 
                                                  create=True,
                                                  validator=self.validators,  
                                                  validationLevel=self.validation_level)
        except OperationFailure:
            # If collection exists, use that collection
            self.__collection__ = MongoCollection(database, self.collection_name)
    
    @property
    def collection(self) -> MongoCollection:
        return self.__collection__
    
    @property
    def model_data(self):
        _data = {}
        for name, field in self.fields.items():
            if isinstance(field, JsonField):
                _data[name] = {}
                for prop_name, prop_field in field.properties.items():
                    _data[name][prop_name] = prop_field.data
            else:
                _data[name] = field.data
        return _data
    
    def set_model_data(self, data: dict):
        self.__data__ = data
        self.__assign_data_to_fields__()

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
            value = self.__data__.get(name)
            if value is not None:
                field.data = value
    
    def serialize_fields(self, document: t.Dict, 
                         fields: t.Union[str, t.List]):
        """Converts to str fields of interest

        Args:
            document (t.Dict): [description]
            fields (t.Union[str, t.List]): [description]

        Raises:
            TypeError: [description]
            ValueError: [description]

        Returns:
            document (t.Dict): [description]
        """
        if not any([isinstance(fields, valid_ins) for valid_ins in [str, list]]):
            raise TypeError('fields param can only be str or list')
        fields_to_serialize = fields if isinstance(fields, list) else [fields]
        for _field in fields_to_serialize:
            if _field not in self._fields.keys():
                # If field does not exists or not a valid field,
                # then continue with the next one
                continue
            document[_field] = str(document[_field])
        return document
