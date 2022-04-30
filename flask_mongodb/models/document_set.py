import typing as t

from copy import deepcopy
from pymongo.cursor import Cursor

from flask_mongodb.core.mixins import InimitableObject


class DocumentSet(InimitableObject):
    def __init__(self, model, *, cursor=None, document=None):
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
            m = deepcopy(self._model)
            m.set_model_data(self.document)
            return m
        return self
    
    def __iter__(self):
        self._check_if_is_cursor(msg='Cannot iterate')
        return iter(self._set)
    
    def __next__(self):
        return next(self._set)
    
    def _check_if_is_cursor(self, msg=None):
        message = msg if msg else 'Cannot call method of DocumentSet without a cursor'
        if not self.cursor:
            raise ValueError(message)
    
    def first(self):
        self._check_if_is_cursor()
        return self._set[0]
    
    def count(self):
        return len(self._set)
    
    def limit(self, limit):
        self._check_if_is_cursor()
        self.cursor = self.cursor.limit(limit)
        if self._set:
            # Clear the set before limiting
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
            # Clear the set before sorting
            self._set.clear()
        for doc in self.cursor:
            m = deepcopy(self._model)
            m.set_model_data(doc)
            self._set.append(m)
        return self
