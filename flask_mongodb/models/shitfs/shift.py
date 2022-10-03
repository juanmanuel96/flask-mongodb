import typing as t

from flask_mongodb import current_mongo
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
            'new_field': False,
            'removed_field': False,
            'field_alteration': False,
            'altered_fields': []
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
        
        old_data: dict = list(self.get_collection_data())
        if not old_data:
            # TODO: Custom exception
            raise Exception('No data in collection')
        old_data = old_data[0]
        collection_schema = self._get_collection_schema()
        schema_properties = collection_schema['$jsonSchema']['properties']
        
        # TODO: Must move this logic to a recursive function due to the object bson type
        # TODO: This logic will ONLY work for changes in existing fields and new fields, not 
        #       field removal
        for name, field in self._model.fields.items():
            if hasattr(field, '_reference'):
                # Reference fields should be skipped
                continue
            if name not in old_data:
                old_fields = old_data.keys()
                missing_fields = [f for f in old_fields if f not in self._model.fields]
                if missing_fields:
                    self.should_shift.update(new_field=True, removed_field=True)
                else:
                    self.should_shift['new_field'] = True
            else:
                # Check that the _id field has not been altered
                if name == '_id':
                    if not isinstance(field.data, type(old_data['_id'])):
                        raise Exception('_id field cannot be altered after creation of'\
                            'collection')
                else:
                    field_definition = schema_properties[name]
                    bson_type: list = field_definition.get('bsonType', [])
                    if 'object' in bson_type:
                        assert isinstance(field, EmbeddedDocumentField)
                        inner_doc = field_definition['properties']
                        for prop_name, prop_field in field.properties.items():
                            if prop_name not in inner_doc:
                                inner_fields = inner_doc.keys()
                                inner_missing_fields = [f for f in inner_fields if f not in field.properties]
                                if inner_missing_fields:
                                    self.should_shift.update(new_field=True, removed_field=True)
                                else:
                                    self.should_shift['new_field'] = True
                    else:
                        if not bson_type:
                            # Only enum type does not have a bsonType
                            if field.bson_type is not None:
                                self.should_shift['field_alteration'] = True
                                self.should_shift['altered_fields'].append(name)
                            if 'enum' in field_definition:
                                pass
                        else:
                            field_bson = field.bson_type[0]
                            if field_bson not in bson_type:
                                self.should_shift['field_alteration'] = True
                                self.should_shift['altered_fields'].append(name)
        print(self.should_shift)
    
    def examine(self):
        if self._model.schemaless:
            return False
        try:
            self.verify()
        except:
            # TODO: Properly manage cases where a collection without data was
            # already created but a shifting is intended
            return False
        return any(list(self.should_shift.values()))
    
    def shift(self):
        if self._model.schemaless:
            # A schemaless model does not require shifting
            return