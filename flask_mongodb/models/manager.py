import typing as t
from bson import ObjectId
from pymongo.results import InsertOneResult

from flask_mongodb.core.exceptions import OperationNotAllowed
from flask_mongodb.core.mixins import InimitableObject
from flask_mongodb.models.document_set import DocumentSet
from flask_mongodb.models.fields import FieldMixin


class BaseManager(InimitableObject):
    def __init__(self, model=None):
        self._model = model
    
    def _clean_filter(self, **filter_to_clean):
        _filter = {}
        for key, value in filter_to_clean.items():
            if hasattr(value, '_is_model'):
                _filter[f'{key}_id'] = value.pk
            else:
                if key in _filter:
                    # Do not overwrite
                    continue
                _filter[key] = value
        return _filter
    
    # Read operations
    def find(self, **filter):
        _filter = self._clean_filter(**filter)
        cursor = self._model.collection.find(_filter)
        docuset = DocumentSet(self._model, cursor=cursor)()
        return docuset
    
    def all(self):
        return self.find()
    
    def find_one(self, **filter):
        if '_id' in filter and isinstance(filter['_id'], str):
            filter['_id'] = ObjectId(filter['_id'])
        _filter = self._clean_filter(**filter)
        doc = self._model.collection.find_one(_filter)
        if doc is None:
            return None
        model = DocumentSet(self._model, document=doc)()
        return model
    
    # Create, Update, Delete (CUD) operations    
    def insert_one(self, insert_data, **options) -> InsertOneResult:
        assert isinstance(insert_data, dict)
        
        data = {}
        
        insert_data.pop('_id', None)
        for key in insert_data.keys():
            attr = getattr(self._model, key, None)
            if hasattr(attr, '_reference'):
                data[f'{key}_id'] = attr.data
            else:
                if key in data:
                    # Do not overwrite anything
                    continue
                data[key] = attr.data
        ack = self._model.collection.insert_one(data, **options)
        return ack
    
    def update_one(self, query, update, update_type='$set', **options):
        assert isinstance(query, dict)
        assert isinstance(update, dict)
        update = {update_type: update}
        ack = self._model.collection.update_one(query, update, **options)
        return ack
    
    def delete_one(self, query, **options):
        """Remove one and only one document"""
        assert isinstance(query, dict)
        ack = self._model.collection.delete_one(query, **options)
        return ack
    
    # Aliases
    get = find_one
    create = insert_one
    update = update_one
    delete = delete_one


class CollectionManager(BaseManager):
    # TODO: Disabled
    # def remove(self, **remove_data):
    #     """Remove current document and all references"""
    #     pass
    pass


class ReferencenManager(BaseManager, FieldMixin):
    _reference_manager = True
    
    def __init__(self, model=None, field_name: str = None):
        super().__init__(model)
        self.field_name = field_name
        self.reference_id = None
    
    def all(self):
        _filter = {
            self.field_name + '_id': self.reference_id
        }
        return super().find(**_filter)
    
    def find(self, **filter):
        if self.field_name + '_id' not in filter:
            filter[self.field_name + '_id'] = self.reference_id
        return super().find(**filter)

    def find_one(self, **filter):
        return super().find_one(**filter)
     
    def insert_one(self, insert_data, **options):
        raise OperationNotAllowed()
    
    def insert_many(self, document_list: t.List[t.Dict], **options):
        raise OperationNotAllowed()
    
    def update_one(self, query, update, update_type='', **options):
        raise OperationNotAllowed()
    
    def delete_one(self, query, **options):
        raise OperationNotAllowed()
