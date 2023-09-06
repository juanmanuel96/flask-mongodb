import typing as t
from bson import ObjectId
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from flask_mongodb.core.exceptions import OperationNotAllowed
from flask_mongodb.core.mixins import InimitableObject
from flask_mongodb.models.document_set import DocumentSet


class BaseManager(InimitableObject):
    def __init__(self, model=None):
        self._model = model
    
    def _clean_query(self, **q):
        _filter = {}
        for key, value in q.items():
            if hasattr(value, '_is_model'):
                _filter[f'{key}_id'] = value.pk
            else:
                if key in _filter:
                    # Do not overwrite
                    continue
                _filter[key] = value
        return _filter
    
    def __getattribute__(self, __name: str) -> t.Any:
        attr = super().__getattribute__(__name)
        if hasattr(attr, '_is_model'):
            attr.connect()
        return attr 
    
    def __getattr__(self, __name):
        return super().__getattr__(__name) 
    
    # Read operations
    def find(self, **filter):
        _filter = self._clean_query(**filter)
        docuset = DocumentSet(self._model, filter=_filter)
        return docuset
    
    def all(self):
        return self.find()
    
    def find_one(self, **filter):
        if '_id' in filter and isinstance(filter['_id'], str):
            filter['_id'] = ObjectId(filter['_id'])
        _filter = self._clean_query(**filter)
        docuset = DocumentSet(self._model, filter=_filter)
        model = docuset.first()
        return model
    
    # Create, Update, Delete (CUD) operations
    def insert_one(self, insert_data: t.Union[None, t.Dict] = None, **options) -> InsertOneResult:
        from flask_mongodb import CollectionModel
        self._model: CollectionModel

        if insert_data:
            insert_data.pop('_id', None)
            for key, value in insert_data.items():
                field = getattr(self._model, key, None)
                if field is None or not hasattr(field, '_model_field'):
                    continue
                field.data = value
            
        insert = self._model.data(exclude=('_id',), include_reference=False)
        ack = self._model.collection.insert_one(insert, **options)
        self._model.pk = ack.inserted_id
        return ack
    
    def update_one(self, query, update, update_type='$set', **options) -> UpdateResult:
        assert isinstance(query, dict)
        assert isinstance(update, dict)
        
        query = self._clean_query(**query)
        update = self._clean_query(**update)
        update = {update_type: update}
        ack = self._model.collection.update_one(query, update, **options)
        return ack
    
    def delete_one(self, query, **options) -> DeleteResult:
        """Remove one and only one document"""
        assert isinstance(query, dict)
        q = self._clean_query(**query)
        ack = self._model.collection.delete_one(q, **options)
        return ack
    
    def delete_many(self, query, **options) -> DeleteResult:
        """Delete all records that match the query"""
        assert isinstance(query, dict)
        q = self._clean_query(**query)
        ack = self._model.collection.delete_many(q, **options)
        return ack
    
    # Aliases
    get = find_one
    create = insert_one
    update = update_one
    delete = delete_one
    delete_all = delete_many


class CollectionManager(BaseManager):
    pass


class ReferenceManager(BaseManager):
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
        if self.field_name + '_id' not in filter:
            filter[self.field_name + '_id'] = self.reference_id
        return super().find_one(**filter)
     
    def insert_one(self, insert_data, **options):
        raise OperationNotAllowed()
    
    def insert_many(self, document_list: t.List[t.Dict], **options):
        raise OperationNotAllowed()
    
    def update_one(self, query, update, update_type='', **options):
        raise OperationNotAllowed()
    
    def delete_one(self, query, **options) -> DeleteResult:
        raise OperationNotAllowed()
    
    def delete_many(self, query, **options) -> DeleteResult:
        raise OperationNotAllowed()
