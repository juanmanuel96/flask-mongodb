import typing as t

from flask_mongodb import current_mongo
from flask_mongodb.core.exceptions import CollectionHasNoData
from flask_mongodb.models.fields import (ArrayField, BooleanField, DatetimeField, StringField, IntegerField, FloatField, 
                                         EmbeddedDocumentField, ObjectIdField)
from ..collection import CollectionModel


MONGODB_BSON_TYPE_MAP = {
    'string': StringField,
    'int32': IntegerField,
    'int64': IntegerField,
    'double': FloatField,
    'object': EmbeddedDocumentField,
    'objectId': ObjectIdField,
    'bool': BooleanField,
    'date': DatetimeField,
    'array': ArrayField
}


class Shift:
    def __init__(self, model: t.Type[CollectionModel]) -> None:
        self._model = model
        self.collection_schema = None
        self.database = current_mongo.connections[self._model.db_alias]
        self.collection = self.database.get_collection(self._model.collection_name)
        self.should_shift = {
            'altered_fields': [],
            'new_fields': [],
            'removed_fields': []
        }
    
    def _get_collection_schema(self):
        collection_options = self.collection.options()
        if collection_options:
            return collection_options['validator']
        else:
            return None
    
    def _get_model_schema(self):
        return self._model.__define_validators__()
    
    def _compare_schemas(self, left: dict, right: dict):
        change = False
        for k in left:
            if change:
                break  # A change was detected, end loop
            if k in right:
                if isinstance(left[k], dict):
                    change = self._compare_schemas(left[k], right[k])
                else:
                    change = left[k] == right[k]
            else:
                change = True
                break  # Detected a change, break the loop
        return change
    
    def get_collection_data(self):
        collection_data = self.collection.find()
        return collection_data
    
    def verify(self):
        """Only applies to models with a schema"""
        collection_schema = self._get_collection_schema()
        old_data: dict = list(self.get_collection_data())
        if not old_data:
            raise CollectionHasNoData('No data in collection')
        old_data = old_data[0]
        schema_properties = collection_schema['$jsonSchema']['properties']
        
        self._compare_model_to_collection(schema_properties, self._model.fields, old_data)
        self._compare_collection_to_model(self._model.fields, old_data)
    
    def _compare_model_to_collection(self, schema_properties: dict, model_fields: dict, 
                                     collection_data: dict, field_path=''):
        """This method will detect model alterations and new fields"""
        for name, field in model_fields.items():
            if field_path:
                _path = field_path + '.' + name
            else:
                _path = name
            
            if hasattr(field, '_reference'):
                # Reference fields should be skipped
                continue
            if name not in collection_data:
                # First check if the field is new
                self.should_shift['new_fields'].append(_path)
            else:
                # Check if the field type has been altered
                if name == '_id':
                    # Check that the _id field has not been altered
                    if not isinstance(field.data, type(collection_data['_id'])):
                        raise Exception('_id field cannot be altered after creation of'\
                            'collection')
                else:
                    field_definition = schema_properties[name]
                    bson_type: list = field_definition.get('bsonType', [])
                    if 'object' in bson_type:
                        # Manage Embedded Document Field
                        assert isinstance(field, EmbeddedDocumentField)
                        inner_data = collection_data[name]
                        inner_properties = field_definition['properties']
                        self._compare_model_to_collection(inner_properties, field.properties, inner_data, 
                                                          _path)
                    else:
                        if not bson_type:
                            # Only enum type does not have a bsonType
                            if field.bson_type is not None:
                                self.should_shift['altered_fields'].append(_path)
                            if 'enum' in field_definition:
                                pass
                        else:
                            field_bson = field.bson_type
                            if field_bson is None and field_bson is not bson_type:
                                self.should_shift['altered_fields'].append(_path)
                            elif field_bson[0] not in bson_type:
                                self.should_shift['altered_fields'].append(_path)
    
    def _compare_collection_to_model(self, model_fields: dict, collection_data: dict, field_path=''):
        """This method is to detect removed fields"""
        for name, data in collection_data.items():
            if field_path:
                _path = field_path + '.' + name
            else:
                _path = name
            
            if name not in model_fields.keys():
                # First check if the field has been removed
                self.should_shift['removed_fields'].append(_path)
            else:
                if name == '_id':
                    # Check that the _id field has not been altered
                    if not isinstance(model_fields['_id'].data, type(data)):
                        raise Exception('_id field cannot be altered after creation of'\
                            'collection')
                else:
                    if isinstance(data, dict):
                        inner_field = model_fields[name].properties
                        self._compare_collection_to_model(inner_field, data, _path)
    
    def examine(self):
        if self._model.schemaless:
            return False
        try:
            self.verify()
        except CollectionHasNoData:
            return True
        except:
            # TODO: Properly manage cases where a collection without data was
            # already created but a shifting is intended
            return False
        return any([len(f) > 0 for f in self.should_shift.values()])
    
    def shift(self):
        if self._model.schemaless:
            # A schemaless model does not require shifting
            return