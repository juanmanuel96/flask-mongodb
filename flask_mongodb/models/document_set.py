import typing as t

from copy import deepcopy
from pymongo.cursor import Cursor


class CollectionManager:
    def __init__(self, model=None):
        self._model = model
    
    def find(self, **filter):
        cursor = self._model.collection.find(filter)
        docuset = DocumentSet(self._model, cursor)()
        return docuset
    
    def find_one(self, **filter):
        pass
    
    def insert(self, **insert_data):
        pass
    
    def insert_one(self, **insert_data):
        pass
    
    def update_one(self, **update_data):
        pass
    
    def delete_one(self, **delete_data):
        """Remove one and only one document"""
        pass
    
    def remove(self, **remove_data):
        """Remove current document and all references"""
        pass


class DocumentSet:
    def __init__(self, model, cursor=None, document=None):
        self._model = model
        self.cursor: Cursor = cursor
        self.document: t.Dict[str, t.Any] = document
        self._set = list()
    
    def __call__(self):
        if self.cursor:
            for doc in self.cursor:
                m = deepcopy(self._model)
                m.set_model_data(doc)
                self._set.append(m)
        else:
            self._model.set_model_data(self.document)
        return self
    
    def __iter__(self):
        self._check_if_is_cursor(msg='Cannot iterate')
        return iter(self._set)
    
    def _check_if_is_cursor(self, msg=None):
        message = msg if msg else 'Cannot call method of DocumentSet without a cursor'
        if not self.cursor:
            raise ValueError(message)
    
    def first(self):
        self._check_if_is_cursor()
        _model = deepcopy(self._model)
        _model.set_model_data(list(self.cursor)[0])
        return _model
    
    def count(self):
        return len(self._set)
    
    def limit(self, limit):
        self._check_if_is_cursor()
        self.cursor = self.cursor.limit(limit)
        if self._set:
            self._set.clear()
        for doc in self.cursor:
            m = deepcopy(self._model)
            m.set_model_data(doc)
            self._set.append(m)
        return self
    
    def sort(self, key_or_list=None, direction=None):
        self._check_if_is_cursor()
        self.cursor = self.cursor.sort(key_or_list=key_or_list, direction=direction)
        if self._set:
            self._set.clear()
        for doc in self.cursor:
            m = deepcopy(self._model)
            m.set_model_data(doc)
            self._set.append(m)
        return self
