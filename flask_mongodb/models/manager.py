import typing as t

from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from flask_mongodb.core.exceptions import OperationNotAllowed
from flask_mongodb.models.document_set import DocumentSet


class BaseManager:
    def __init__(self, model=None):
        from flask_mongodb.models import CollectionModel
        self._model: CollectionModel = model
    
    def _clean_query(self, **q):
        """
        This is for searching
        :param q: Keyword argument for key value items to include in query filter
        :return: Dictionary for MongoDB to query for.
        """
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
    def run_save(self, session: t.Optional[ClientSession] = None, bypass_validation=False,
                 comment: t.Optional[str] = None) -> t.Union[InsertOneResult, UpdateResult]:
        model_pk = self._model.pk
        if model_pk is None:
            # It is a new item
            insert_data = self._model.modified_fields(insert=True)
            ack = self._model.collection.insert_one(insert_data,
                                                    session=session,
                                                    bypass_document_validation=bypass_validation,
                                                    comment=comment)
            self._model['_id'] = ack.inserted_id
        else:
            # Must do an update
            modified_fields = self._model.modified_fields()
            ack = self._model.collection.update_one(
                {'_id': self._model.pk},
                {
                    '$set': modified_fields
                },
                session=session, bypass_document_validation=bypass_validation, comment=comment
            )

        return ack

    def run_delete(self, session: t.Optional[ClientSession] = None, comment: t.Optional[str] = None, **options):
        ack = self._model.collection.delete_one({'_id': self._model.pk}, session=session, comment=comment,
                                                **options)
        return ack

    def insert_one(self, **insert_data):
        if not insert_data:
            raise ValueError('Must provide data to insert')

        insert_data.pop('_id', None)
        for key, value in insert_data.items():
            field = getattr(self._model, key, None)
            if field is None or not hasattr(field, '_model_field'):
                continue
            field.set_data(value)

        insert = self._model.modified_fields(insert=True)
        ack = self._model.collection.insert_one(insert)
        self._model['_id'] = ack.inserted_id
        return self._model
    
    def update_one(self, query, update, update_type='$set', **options):
        assert isinstance(query, dict)
        assert isinstance(update, dict)
        
        query = self._clean_query(**query)
        update = self._clean_query(**update)
        update = {update_type: update}
        ack = self._model.collection.update_one(query, update, **options)
        if not ack.acknowledged:
            # TODO: Custom Exception
            raise Exception('Insert not acknowledged')
        return self.find_one(**query)
    
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
