import typing as t
import logging

from copy import deepcopy

from bson import ObjectId

from flask_mongodb.core.exceptions import CollectionException, FieldError
from flask_mongodb.core.wrappers import MongoCollection
from flask_mongodb.models.fields import (EmbeddedDocumentField, EnumField,
                                         ObjectIdField, ReferenceIdField,
                                         StructuredArrayField)
from flask_mongodb.models.manager import CollectionManager, ReferencenManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class BaseCollection:
    _is_model = True
    collection_name: str = None
    schemaless = False
    validation_level: str = 'strict'
    manager_class = CollectionManager
    db_alias = 'main'
    _id = ObjectIdField()
    
    def __init__(self) -> None:
        self._fields = dict()
        self.__collection__: MongoCollection = None
        if not self.manager_class:
            raise ValueError('Missing collection manager class')
        self._manager = self.manager_class(self)
        setattr(self, '_id', self._id)
        setattr(self, 'db_alias', self.db_alias)
        self._fields['_id'] = self._id
        self._connected = False
        
        # Prepare _fields attribute
        for name in dir(self):
            if not name.startswith('_'):
                attr = getattr(self, name)
                if hasattr(attr, '_model_field'):
                    # Copy the field
                    self._fields[name] = deepcopy(attr)
                    if hasattr(attr, '_reference'):
                        attr: ReferenceIdField
                        related_name = attr.related_name
                        if related_name is None:
                            related_name = str(self) + '_related'
                        setattr(attr.model, related_name, ReferencenManager(self, name))
                        setattr(self, f'{name}_id', ObjectIdField())
                        self._fields[f'{name}_id'] = getattr(self, f'{name}_id')

    def __setitem__(self, __name: str, __value: t.Any):
        # Dict style assignment
        field = self._fields.get(__name, None)
        
        if field is None:
            raise KeyError(f'CollectionModel does not field with name {__name}')
        if hasattr(__value, '_model_data'):
            raise ValueError('Cannot assign model field to this model field')
        
        field.data = __value
        if hasattr(field, '_reference'):
            self.fields[f'{__name}_id'].data = __value
            
    
    def __getitem__(self, __name: str):
        # Dict style getting
        field = self._fields.get(__name, None)
        if field is None:
            raise KeyError(f'Not a valid field with name {__name}')
        if hasattr(field, '_reference'):
            return field.reference
        return field.data
    
    def __getattribute__(self, __name: str) -> t.Any:
        attr = super().__getattribute__(__name)
        if hasattr(attr, '_reference_manager'):
            attr.reference_id = self['_id']
        return attr 
    
    def __getattr__(self, __name):
        return super().__getattr__(__name) 
    
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
    
    def __define_validators__(self):
        """
        DEPRECATED: This method will be removed as of version 2
        """
        validators = {
            '$jsonSchema': {
                "bsonType": "object",
                "required": [],
                "properties": {}
            }
        }
        for name, field in self.fields.items():
            if isinstance(field, ReferenceIdField):
                # If field is a ReferenceIdField, it will be ignored and it's counterpart [name]_id
                # will be used
                continue
            
            if hasattr(field, '_reference_manager'):
                # Do not consider reference managers
                continue
            
            if field.required:
                validators["$jsonSchema"]["required"].append(name)
            
            validators['$jsonSchema']['properties'][name] = {}
            
            # Defining field BSON types
            if field.bson_type is not None:
                # If bson_type attrib is not None, add it to the bson_types
                # Need to copy to avoid refrence modifications
                validators['$jsonSchema']["properties"][name].update({"bsonType": deepcopy(field.bson_type)})

                # Check if null is allowed and add it
                if field.allow_null:
                    validators["$jsonSchema"]["properties"][name]["bsonType"].append('null')

            # Add min_length if it has it, applies only to StringField and PasswordField
            if min_length := getattr(field, 'min_length', None):
                validators["$jsonSchema"]["properties"][name].update({'minLength': min_length})
            
            # Add max_length if it has it
            if max_length := getattr(field, 'max_length', None):
                validators["$jsonSchema"]["properties"][name].update({'maxLength': max_length})
            
            if field.description:
                validators["$jsonSchema"]["properties"][name].update({'description': field.description})
            
            if isinstance(field, EnumField):
                enums = self._enum_field_validators(field)
                validators['$jsonSchema']['properties'][name].update({'enum': enums})
            elif isinstance(field, EmbeddedDocumentField):
                embedded_validators = self._embedded_document_validators(field)
                validators['$jsonSchema']['properties'][name].update(embedded_validators)
            elif isinstance(field, StructuredArrayField):
                structured_array_validators = self._structured_array_validators(field)
                validators['$jsonSchema']['properties'][name].update(structured_array_validators)
            else:
                # It's another field, continue on
                pass
        
        if not validators['$jsonSchema'].get('required'):
            validators['$jsonSchema'].pop('required')  # Remove required field if empty list
        return validators if validators['$jsonSchema']['properties'] else {}
    
    def _enum_field_validators(self, field):
        if field.bson_type is not None:
            raise FieldError('The enum of the EnumField will establish the valid types')
        
        enum = {'enum': field.enum}
        if field.allow_null:
            enum['enum'].append('null')
        return enum['enum']
    
    def _embedded_document_validators(self, field: EmbeddedDocumentField):
        sub_validators = {
            "bsonType": ['object'],
            "required": [],
            "properties": {}
        }
        
        if field.allow_null:
            sub_validators['bsonType'].append('null')
        
        for prop_name, prop_field in field.properties.items():
            if prop_field.required:
                sub_validators["required"].append(prop_name)
            
            sub_validators['properties'][prop_name] = {}
            
            # Defining field BSON types
            if prop_field.bson_type is not None:
                sub_validators["properties"][prop_name].update({"bsonType": deepcopy(prop_field.bson_type)})

                # If has BSON Type, check if null is allowed and add it
                if prop_field.allow_null:
                    sub_validators['properties'][prop_name]["bsonType"].append('null')
            
            if max_length := getattr(prop_field, 'max_length', None):
                sub_validators["properties"][prop_name].update({'maxLength': max_length})

            if min_length := getattr(prop_field, 'min_length', None):
                sub_validators["properties"][prop_name].update({'minLength': min_length})
            
            if prop_field.description:
                sub_validators['properties'][prop_name].update({'description': prop_field.description})
            
            if isinstance(prop_field, EnumField):
                in_enum = self._enum_field_validators((prop_field))
                sub_validators['properties'][prop_name].update(enum=in_enum)
            elif isinstance(prop_field, EmbeddedDocumentField):
                # Support for Embedded documents in embedded documents
                sub_sub_validators = self._embedded_document_validators(prop_field)
                sub_validators['properties'][prop_name].update(sub_sub_validators)
            elif isinstance(prop_field, StructuredArrayField):
                struc_array_validators = self._structured_array_validators(prop_field)
                sub_validators['properties'][prop_name].update(struc_array_validators)
            else:
                # It's another field, continue on
                pass
    
        if not sub_validators['required']:
            sub_validators.pop('required', None)  # If required field empty, remove it
        
        return sub_validators

    def _structured_array_validators(self, field: StructuredArrayField):
        field_properties = {}
        if min_items := getattr(field, 'min_items', None):
            field_properties.update({'min_items': min_items})
        
        if max_items := getattr(field, 'max_items', None):
            field_properties.update({'max_items': max_items})
        
        items = {
            'bsonType': ['object'],
            'required': [],
            'properties': {}
        }
        
        for item_name, item_field in field.items.items():
            if item_field.required:
                items['required'].append(item_name)
            
            items['properties'][item_name] = {}
            
            if item_field.bson_type is not None:
                items['properties'][item_name].update({'bsonType': deepcopy(item_field.bson_type)})
                
                if item_field.allow_null:
                    items[item_name]['properties']['bsonType'].append('null')
            
            # Add max_length if it has it
            if max_length := getattr(item_field, 'max_length', None):
                items["properties"][item_name].update({'maxLength': max_length})

            # Add min_length if it has it
            if min_length := getattr(item_field, 'min_length', None):
                items["properties"][item_name].update({'minLength': min_length})
            
            if item_field.description:
                items['properties'][item_name].update(description=item_field.description)
            
            if isinstance(item_field, EmbeddedDocumentField):
                sub_validators = self._embedded_document_validators(item_field)
                items['properties'][item_name].update(sub_validators)
            elif isinstance(item_field, EnumField):
                in_enum = self._enum_field_validators(item_field)
                items['properties'][item_name].update({'enum': in_enum})
            elif isinstance(item_field, StructuredArrayField):
                struc_array_validators = self._structured_array_validators(item_field)
                items['properties'][item_name].update(struc_array_validators)
            else:
                # It's another field, continue on
                pass
        
        if not items['required']:
            items.pop('required', None)
        
        field_properties.update(items=items)
        return field_properties

    @property
    def manager(self) -> CollectionManager:
        return self._manager
    
    @property
    def fields(self) -> dict:
        return self._fields
    
    @property
    def pk(self):
        return self._id.data
    
    @pk.setter
    def pk(self, value):
        self._id.data = value
    
    def get_collection_schema(self):
        return self.__define_validators__()
    
    def connect(self):
        """Connect directly to the MongoDB Collection"""
        if self._connected:
            # Don't connect again
            return None
        from flask_mongodb import current_mongo
        db = current_mongo.connections[self.db_alias]
        self.__collection__ = MongoCollection(db, self.collection_name)
        self._connected = True
    
    def disconnect(self):
        self.__collection__ = None
        self._connected = False


class CollectionModel(BaseCollection):
    def __init__(self, **field_values):
        self._initial = {} if not field_values else field_values
        self._update = {}
        super(CollectionModel, self).__init__()
        
        if not self.collection_name:
            raise CollectionException('Need to specify the collection_name')
        
        if not self.db_alias:
            raise CollectionException('Need to the specify the db_alais')
        
        for name, field in self._fields.items():
            # Make fields accessible by the dot convension and obscure class attribute
            # names
            setattr(self, name, field)
        
        if self._initial:
            self.__assign_data_to_fields__()
        
        self.schema_validators = None
    
    def __assign_data_to_fields__(self):
        for name in self.fields.keys():
            value = self._initial.get(name)
            if value is None:
                # Ignore fields that do not exist
                continue
            self[name] = value
            if hasattr(self.fields[name], '_reference') and self.fields[name].data:
                self[f'{name}_id'] = value
        
        # Check for reference fields
        for name, field in self.fields.items():
            if hasattr(field, '_reference'):
                id_field_of_ref = self[name + '_id']
                if str(field.data) != str(id_field_of_ref):
                    field.data = id_field_of_ref
    
    def data(self, as_str=False, exclude=(), include_reference=True, include_all_references=False):
        """DEPRECATED; This method will be remove in version 2"""
        
        logger.warning('DEPRECATED: The `data` method is deprecated and will be removed in version 2')
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
                    continue  # Go to next field
                _data[name] = field.reference.data(as_str, exclude, 
                                                    include_reference=include_all_references,
                                                    include_all_references=include_all_references)
            else:
                if isinstance(field, ReferenceIdField):
                    # If the field is a reference field, do not get the data
                    continue
                _data[name] = field.data if not as_str else str(field.data)
        return _data
    
    def set_model_data(self, data: dict):
        self._initial = data
        self.__assign_data_to_fields__()
    
    @property
    def collection(self) -> t.Union[MongoCollection, None]:
        return self.__collection__
