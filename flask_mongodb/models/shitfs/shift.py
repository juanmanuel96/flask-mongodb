import typing as t
from copy import copy

from flask_mongodb.cli.utils import define_schema_validator
from flask_mongodb.core.wrappers import MongoDatabase
from flask_mongodb.models.collection import CollectionModel
from flask_mongodb.models.fields import (ArrayField, BooleanField, DatetimeField, Field, StringField, IntegerField,
                                         FloatField,
                                         EmbeddedDocumentField, ObjectIdField)

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
    def __init__(self, model_class: t.Type[CollectionModel]) -> None:
        self._model = model_class()
        self.collection_schema = None
        self.should_shift = {
            'altered_fields': [],
            'new_fields': [],
            'removed_fields': []
        }
        self._model_schema = {}

    def _get_database(self) -> MongoDatabase:
        from flask_mongodb import current_mongo
        database = current_mongo.connections[self._model.db_alias]
        return database

    def _get_collection(self, database: MongoDatabase):
        collection = database.get_collection(self._model.collection_name)
        return collection

    def _get_collection_schema(self):
        db = self._get_database()
        collection = self._get_collection(db)
        collection_options = collection.options()
        if collection_options:
            return collection_options['validator']
        else:
            return None

    def _set_model_schema(self):
        self._model_schema = define_schema_validator(self._model)

    def _get_model_schema(self):
        return self._model_schema

    def _compare_model_to_collection(self, schema_properties: dict, model_fields: t.Dict, field_path=''):
        """This method will detect model alterations and new fields"""
        for name, field in model_fields.items():
            if field_path:
                _path = field_path + '.' + name
            else:
                _path = name

            if hasattr(field, '_reference'):
                # Reference fields should be skipped
                continue

            if name not in schema_properties.keys():
                # First check if the field is new
                self.should_shift['new_fields'].append(_path)
            else:
                # Check if the field type has been altered
                if name == '_id':
                    # Check that the _id field has not been altered, it is still an ObjectIdField
                    if not isinstance(field, ObjectIdField):
                        # TODO: Custom Exception
                        raise Exception('_id field cannot be altered after creation of collection and must be'
                                        'ObjectIdField')
                else:
                    field_properties = schema_properties[name]
                    bson_type: t.Optional[t.List] = field_properties.get('bsonType')
                    # First must check if bson_type is an EnumField
                    if bson_type is None:  # Is Enum type
                        # Only enum type does not have a bsonType
                        if field.bson_type is not bson_type:
                            # This means it is no longer an EnumField
                            self.should_shift['altered_fields'].append(_path)
                    elif 'object' in bson_type:
                        # Manage Embedded Document Field
                        inner_properties = field_properties['properties']
                        self._compare_model_to_collection(inner_properties, field.properties, field_path=_path)
                    else:
                        field_bson: t.List = copy(field.bson_type)  # Get the field's bson_type attribute
                        if field.allow_null:
                            field_bson.append('null')

                        if field_bson is None and bson_type is not None:
                            # Field was altered to a EnumField type
                            self.should_shift['altered_fields'].append(_path)
                        elif field_bson != bson_type:
                            # The field bson_type attribute is a list and is not the same as the schema BSON type
                            # of the field (such as adding a `null` option)
                            self.should_shift['altered_fields'].append(_path)

    def _compare_collection_to_model(self, model_fields: dict,
                                     schema_properties: t.Optional[t.Dict] = None,
                                     field_path=''):
        """This method is to detect removed fields"""
        name: str
        bson_type: t.List[str]
        for name, properties in schema_properties.items():
            if field_path:
                _path = field_path + '.' + name
            else:
                _path = name

            if name not in schema_properties.keys():
                # TODO: Custom Exception
                raise Exception(f'Cannot modify schema directly. Field name: {_path}')
            else:
                if 'object' in properties.get('bson_type', []):
                    embedded_field = model_fields[name].properties
                    embedded_schema = properties['properties']
                    self._compare_collection_to_model(embedded_field, embedded_schema, field_path=_path)
                else:
                    if name not in self._model.fields.keys():
                        self.should_shift['removed_fields'].append(name)

    def get_collection_data(self):
        db = self._get_database()
        collection = self._get_collection(db)
        collection_data = collection.find()
        return collection_data

    def verify(self):
        """Only applies to models with a schema"""
        collection_schema = self._get_collection_schema()
        schema_properties = collection_schema['$jsonSchema']['properties']

        self._compare_model_to_collection(schema_properties, self._model.fields)
        self._compare_collection_to_model(self._model.fields, schema_properties)

    def examine(self):
        if self._model.schemaless:
            return False

        self.verify()
        return any([True if f else False for f in self.should_shift.values()])

    def shift(self):
        def _find_embedded_property_default(embedded_field: EmbeddedDocumentField, _p_path: list):
            prop_name = _p_path.pop()
            doc_property: Field = embedded_field[prop_name]
            if isinstance(doc_property, EmbeddedDocumentField):
                return _find_embedded_property_default(doc_property, _p_path)
            else:
                return doc_property.data

        examine = self.examine()
        if not examine:
            # If nothing has to be done, then exit
            # TODO: Make a better exit that provides better information
            return False

        db = self._get_database()
        collection = self._get_collection(db)
        field_path: str

        # First manage fields that have been removed
        for field_path in self.should_shift['removed_fields']:
            collection.update_many({}, {'$unset': {field_path: 1}}, bypass_document_validation=True)

        # Then add new fields
        for field_path in self.should_shift['new_fields']:
            if '.' in field_path:
                # New field in an embedded document
                property_path = field_path.split('.')
                field = property_path.pop(0)
                model_field = self._model.fields[field]
                value = _find_embedded_property_default(model_field, property_path)
            else:
                model_field = self._model.fields[field_path]
                value = model_field.data
            collection.update_many({}, {'$set': {field_path: value}}, bypass_document_validation=True)

        # Finally, modify altered fields
        # TODO: EnumField during an update will set all with the default value, should first check if existing
        #  value is in choices and leave that one as such, otherwise use the default
        for field_path in self.should_shift['altered_fields']:
            if '.' in field_path:
                property_path = field_path.split('.')
                field = property_path.pop(0)
                model_field = self._model.fields[field]
                value = _find_embedded_property_default(model_field, property_path)
            else:
                model_field = self._model.fields[field_path]
                value = model_field.data
            collection.update_many({}, {'$set': {field_path: value}}, bypass_document_validation=True)

        # Create the new schema
        self._set_model_schema()
        new_schema = self._get_model_schema()
        db.command('collMod', self._model.collection_name,
                   validator=new_schema,
                   validationLevel=self._model.validation_level)
        return True
