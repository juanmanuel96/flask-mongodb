from flask_mongodb.core.mixins import InimitableObject
from flask_mongodb.models.document_set import DocumentSet


class CollectionManager(InimitableObject):
    def __init__(self, model=None):
        self._model = model
    
    def find(self, **filter):
        cursor = self._model.collection.find(filter)
        docuset = DocumentSet(self._model, cursor)()
        return docuset
    
    def find_one(self, **filter):
        cursor = self._model.collection.find(filter)
        docuset = DocumentSet(self._model, cursor)()
        return docuset.first()
    
    def insert(self, insert_data, **options):
        pass
    
    def insert_one(self, insert_data, **options):
        assert isinstance(insert_data, dict)
        insert_data.pop('_id', None)
        ack = self._model.collection.insert_one(insert_data, **options)
        return ack
    
    def update_one(self, query, update, **options):
        assert isinstance(query, dict)
        assert isinstance(update, dict)
        ack = self._model.collection.update_one(query, update, **options)
        return ack
    
    def delete_one(self, **delete_data):
        """Remove one and only one document"""
        pass
    
    def remove(self, **remove_data):
        """Remove current document and all references"""
        pass