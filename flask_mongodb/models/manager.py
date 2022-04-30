import typing as t
from bson import ObjectId

from flask_mongodb.core.mixins import InimitableObject
from flask_mongodb.models.document_set import DocumentSet


class CollectionManager(InimitableObject):
    def __init__(self, model=None):
        self._model = model
    
    # Read operations
    def find(self, **filter):
        cursor = self._model.collection.find(filter)
        docuset = DocumentSet(self._model, cursor=cursor)()
        return docuset
    
    def find_one(self, **filter):
        if '_id' in filter and isinstance(filter['_id'], str):
            filter['_id'] = ObjectId(filter['_id'])
        doc = self._model.collection.find_one(filter)
        if doc is None:
            return None
        model = DocumentSet(self._model, document=doc)()
        return model
    
    # Create, Update, Delete (CUD) operations
    def insert_many(self, document_list: t.List[t.Dict], **options):
        assert isinstance(document_list, list)
        assert all([isinstance(doc, dict) for doc in document_list])
        # Cleaning doc list
        clean_list = [(doc, doc.pop('_id', None))[0] for doc in document_list]
        ack = self._model.collection.insert_many(clean_list, **options)
        return ack
    
    def insert_one(self, insert_data, **options):
        assert isinstance(insert_data, dict)
        insert_data.pop('_id', None)
        ack = self._model.collection.insert_one(insert_data, **options)
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
    
    def remove(self, **remove_data):
        """Remove current document and all references"""
        pass
