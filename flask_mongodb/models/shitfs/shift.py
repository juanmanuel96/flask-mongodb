import typing as t
from copy import copy

from flask_mongodb.cli.utils import define_schema_validator
from flask_mongodb.core.exceptions import NoDatabaseShiftingRequired, idUnmodifiable
from flask_mongodb.core.wrappers import MongoDatabase
from flask_mongodb.models.collection import CollectionModel
from flask_mongodb.models.fields import (ArrayField, BooleanField, DatetimeField, Field, StringField, IntegerField,
                                         FloatField, EnumField,
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
    'array': ArrayField,
    None: EnumField
}


class Shift:
    def __init__(self, model_class: t.Type[CollectionModel]) -> None:
        self._model = model_class()
        self.collection_schema = None
        self.new_fields: t.List[str] = []
        self.removed_fields: t.List[str] = []
        self.altered_fields: t.Dict[str, t.Dict[str, bool]] = {}
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

    def _compare_model_to_collection(self, schema: dict, model_fields: t.Dict, field_path=''):
        """This method will detect model alterations and new fields"""
        for name, field in model_fields.items():
            # This is to build the path to properties in an embedded document
            if field_path:
                _path = field_path + '.' + name
            else:
                _path = name

            # Reference fields are skipped
            if hasattr(field, '_reference'):
                # Reference fields should be skipped
                continue

            schema_properties: t.Dict[str, t.Any] = schema['properties']
            required_fields: t.List[str] = schema['required']

            if name not in schema_properties.keys():
                # First check if the field is new
                self.new_fields.append(_path)
            else:
                # Detect any changes in the field
                if name == '_id':
                    # Check that the _id field has not been altered, it is still an ObjectIdField
                    if not isinstance(field, ObjectIdField):
                        raise idUnmodifiable('_id field cannot be altered after creation of collection and must be'
                                             'ObjectIdField')
                else:
                    field_schema_properties = schema_properties[name]
                    bson_type: t.Optional[t.List] = field_schema_properties.get('bsonType')

                    if bson_type is None:
                        # First must check if bson_type None for EnumField, if None originally Enum
                        if field.bson_type is not bson_type:
                            # This means it is no longer an EnumField
                            self.altered_fields.update({
                                _path:
                                    {
                                        'new': type(field)
                                    }
                            })
                    elif 'object' in bson_type:
                        # Manage Embedded Document Field
                        self._compare_model_to_collection(field_schema_properties, field.properties,
                                                          field_path=_path)
                    else:
                        field_bson: t.List = copy(field.bson_type)  # Get the field's bson_type attribute
                        if field.allow_null:
                            field_bson.append('null')

                        if field_bson is None and bson_type is not None:
                            # Field was altered to a EnumField type
                            self.altered_fields.update({
                                _path: {
                                    'replace': True
                                }
                            })
                        elif field_bson != bson_type:
                            # The field bson_type attribute is a list and is not the same as the schema BSON type
                            # of the field (such as adding a `null` option)
                            self.altered_fields.update({
                                _path: {
                                    'replace': True
                                }
                            })

                    required_change = None
                    if field.required and name not in required_fields:
                        # Field required status got enabled
                        required_change = True
                    elif not field.required and name in required_fields:
                        # Field required status got disabled
                        required_change = False
                    else:
                        # Required status remains unchanged
                        pass

                    if required_change is not None:
                        if _path not in self.altered_fields.keys():
                            self.altered_fields[_path] = {
                                'replace': False
                            }
                        self.altered_fields[_path]['required'] = required_change

    def _compare_collection_to_model(self, model_fields: t.Dict, schema: t.Dict, field_path=''):
        """This method is to detect removed fields"""
        name: str
        bson_type: t.List[str]
        schema_properties = schema['properties']
        for name, properties in schema_properties.items():
            if field_path:
                _path = field_path + '.' + name
            else:
                _path = name

            if name not in schema_properties.keys():
                raise ValueError(f'Cannot modify schema directly. Field name: {_path}')
            else:
                if 'object' in properties.get('bson_type', []):
                    embedded_field = model_fields[name].properties
                    embedded_schema = properties['properties']
                    self._compare_collection_to_model(embedded_field, embedded_schema, field_path=_path)
                else:
                    if name not in self._model.fields.keys():
                        if name == '_id':
                            raise idUnmodifiable('Cannot delete _id field')
                        self.removed_fields.append(name)

    def get_collection_data(self):
        db = self._get_database()
        collection = self._get_collection(db)
        collection_data = collection.find()
        return collection_data

    def verify(self):
        """Only applies to models with a schema"""
        collection_schema = self._get_collection_schema()
        schema = collection_schema['$jsonSchema']

        # This section will verify which fields have modified, created, or deleted
        self._compare_model_to_collection(schema, self._model.fields)
        self._compare_collection_to_model(self._model.fields, schema)
        return any(self.removed_fields) or any(self.new_fields) or any(self.altered_fields.keys())

    def examine(self) -> bool:
        if self._model.schemaless:
            return False

        changes = self.verify()
        return changes

    def shift(self):
        def _find_embedded_property_default(embedded_field: EmbeddedDocumentField, _p_path: list):
            prop_name = _p_path.pop(0)  # Get the top level field name
            doc_property: Field = embedded_field.properties[prop_name]
            if isinstance(doc_property, EmbeddedDocumentField):
                return _find_embedded_property_default(doc_property, _p_path)
            else:
                return doc_property.data

        examine = self.examine()
        if not examine:
            raise NoDatabaseShiftingRequired()

        db = self._get_database()
        collection = self._get_collection(db)
        field_path: str

        # First manage fields that have been removed
        for field_path in self.removed_fields:
            collection.update_many({}, {'$unset': {field_path: 1}})

        # Then add new fields
        for field_path in self.new_fields:
            if '.' in field_path:
                # New field in an embedded document
                property_path = field_path.split('.')
                field = property_path.pop(0)
                model_field = self._model.fields[field]
                value = _find_embedded_property_default(model_field, property_path)
            else:
                model_field = self._model.fields[field_path]
                value = model_field.data
            collection.update_many({}, {'$set': {field_path: value}})

        # Finally, modify altered fields
        for field_path, mod in self.altered_fields.items():
            if mod['replace']:
                if '.' in field_path:
                    property_path = field_path.split('.')
                    field = property_path.pop(0)
                    model_field = self._model.fields[field]
                    value = _find_embedded_property_default(model_field, property_path)
                else:
                    model_field = self._model.fields[field_path]
                    value = model_field.data
                collection.update_many({}, {'$set': {field_path: value}})

        # Create the new schema
        self._set_model_schema()
        new_schema = self._get_model_schema()
        db.command('collMod', self._model.collection_name,
                   validator=new_schema,
                   validationLevel=self._model.validation_level)
        return True
