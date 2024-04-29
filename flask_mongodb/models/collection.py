import logging
import typing as t
from copy import deepcopy

from bson.json_util import dumps as bson_dumps

from flask_mongodb.core.exceptions import CollectionException
from flask_mongodb.core.wrappers import MongoCollection
from flask_mongodb.models.fields import (EmbeddedDocumentField, ObjectIdField, ReferenceIdField, Field)
from flask_mongodb.models.manager import CollectionManager, ReferenceManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class BaseCollection:
    _is_model = True
    collection_name: str = None
    schemaless = False
    validation_level: str = 'strict'
    manager_class = CollectionManager
    db_alias = 'main'
    _id = ObjectIdField(allow_null=True, default=None)

    def __init__(self, **field_values) -> None:
        self._fields: t.Dict = dict()
        self.__collection__: t.Optional[MongoCollection] = None
        if not self.manager_class:
            raise ValueError('Missing collection manager class')
        self._manager = self.manager_class(self)
        setattr(self, '_id', self._id)
        setattr(self, 'db_alias', self.db_alias)
        self._fields['_id'] = self._id
        self._connected = False

        # Prepare _fields attribute
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, '_model_field'):
                # Copy the field
                self._fields[name] = deepcopy(attr)
                if hasattr(attr, '_reference'):
                    attr: ReferenceIdField
                    related_name = attr.related_name
                    if related_name is None:
                        related_name = str(self) + '_related'
                    setattr(attr.model, related_name, ReferenceManager(self, name))

                    # Set model reference data
                    setattr(self, f'{name}_id', ObjectIdField())
                    self._fields[f'{name}_id'] = getattr(self, f'{name}_id')

        self._initial = {**field_values}

    def __setitem__(self, __name: str, __value: t.Any):
        # Dict style assignment
        field = self._fields.get(__name, None)

        if field is None:
            raise KeyError(f'CollectionModel does not field with name {__name}')

        field.set_data(__value)
        if hasattr(field, '_reference'):
            self.fields[f'{__name}_id'].set_data(__value)

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
        obj._connected = False
        return obj

    def _incoming_data_to_fields(self, incoming: t.Dict, initial=False):
        for name, field in self.fields.items():
            try:
                value = incoming[name]
            except KeyError:
                # If cannot find field in incoming, keep same field value
                continue

            field.set_data(value)
            if initial:
                field.set_initial(value)

        # Check for reference fields
        for name, field in self.fields.items():
            if hasattr(field, '_reference'):
                id_field_of_ref = getattr(self, f'{name}_id')
                if str(field.get_data()) != str(id_field_of_ref.get_data()):
                    field.set_data(id_field_of_ref.get_data())
                    if initial:
                        field.set_initial(id_field_of_ref.get_data())

    def _get_embedded_document(self, document_obj: t.Dict, _field_name: str,
                               _field: t.Union[EmbeddedDocumentField, Field]):
        document_obj[_field_name] = {}
        for prop_name, prop_field in _field.properties.items():
            if isinstance(_field, EmbeddedDocumentField):
                self._get_embedded_document(document_obj[_field_name], prop_name, prop_field)
            else:
                document_obj[_field_name].update({prop_name: prop_field.data})

    def _traverse_embedded_document(self, change_obj: t.Dict, _name: str,
                                    _field: t.Union[Field, EmbeddedDocumentField]):
        for prop_name, prop_field in _field.properties.items():
            _path = f'{_name}.{prop_name}'
            if isinstance(prop_field, EmbeddedDocumentField):
                self._traverse_embedded_document(change_obj, prop_name, prop_field)
            else:
                if prop_field.get_data() != prop_field.get_initial():
                    change_obj[_path] = prop_field.get_data()

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
        self._id.set_data(value)

    def modified_fields(self, insert=False) -> t.Dict[str, t.Any]:
        def _traverse_embedded_document(change_obj: t.Dict, _name: str,
                                        _field: t.Union[Field, EmbeddedDocumentField], _insert=False):
            for prop_name, prop_field in _field.properties.items():
                _path = f'{_name}.{prop_name}'
                if isinstance(prop_field, EmbeddedDocumentField):
                    _traverse_embedded_document(change_obj, prop_name, prop_field)
                else:
                    if prop_field.get_data() != prop_field.get_initial():
                        change_obj[_path] = prop_field.get_data()

        change = {}
        for name, field in self._fields.items():
            if name == '_id':
                # Skip _id field, it should not be considered as a modified field
                continue
            if isinstance(field, EmbeddedDocumentField):
                if insert:
                    self._get_embedded_document(change, name, field)
                else:
                    self._traverse_embedded_document(change, name, field)
            else:
                if field.get_data() != field.get_initial() and not insert:
                    change[name] = field.get_data()
                else:
                    change[name] = field.get_data()
        return change

    def connect(self):
        """
        Connect to the MongoDB Collection
        """
        if not self._connected:
            from flask_mongodb import current_mongo

            db = current_mongo.connections[self.db_alias]
            self.__collection__ = MongoCollection(db, self.collection_name)
            self._connected = True

        return self

    def disconnect(self):
        self.__collection__ = None
        self._connected = False

        return self

    def save(self, session=None, bypass_validation=False, comment=None):
        return self.manager.run_save(session, bypass_validation, comment)

    def delete(self, session=None, comment=None):
        return self.manager.run_delete(session, comment)


class CollectionModel(BaseCollection):
    def __init__(self, **field_values):
        super().__init__(**field_values)

        if not self.collection_name:
            raise CollectionException('Need to specify the collection_name')

        if not self.db_alias:
            raise CollectionException('Need to the specify the db_alais')

        for name, field in self._fields.items():
            # Make fields accessible by the dot conversion and obscure class attribute
            # names
            setattr(self, name, field)

        self._incoming_data_to_fields(self._initial, initial=True)

        self.schema_validators = None

    def to_document(self, json_parsed=False, exclude=tuple()):
        def _get_embedded_document(document_obj: t.Dict, _field_name: str,
                                   _field: t.Union[EmbeddedDocumentField, Field]):
            document_obj[_field_name] = {}
            for prop_name, prop_field in _field.properties.items():
                if isinstance(prop_field, EmbeddedDocumentField):
                    _get_embedded_document(document_obj[_field_name], prop_name, prop_field)
                else:
                    document[name][prop_name] = prop_field.data

        document = {}
        for name, field in self.fields.items():
            if name in exclude:
                continue  # Go to next one
            if isinstance(field, EmbeddedDocumentField):
                _get_embedded_document(document, name, field)
            elif isinstance(field, ObjectIdField):
                if name not in document:
                    document[name] = field.data
            elif isinstance(field, ReferenceIdField):
                ref = field.reference
                ref_name = f'{name}_id'
                if ref_name in exclude:
                    # Go to the next one if the reference id field is excluded
                    continue
                if ref is None:
                    # This should raise an error since the object referenced by another must not be deleted before
                    # the one referencing
                    document[ref_name] = ref
                else:
                    document[ref_name] = ref.pk
            else:
                document[name] = field.data

        if json_parsed:
            return bson_dumps(document)
        return document

    def set_model_data(self, data: t.Dict, initial=False):
        self._incoming_data_to_fields(data, initial)
        return self

    @property
    def collection(self) -> t.Union[MongoCollection, None]:
        return self.__collection__
