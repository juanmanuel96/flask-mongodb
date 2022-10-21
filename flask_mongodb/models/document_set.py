import typing as t

from copy import deepcopy
from pymongo.cursor import Cursor
from pymongo import DESCENDING

from flask_mongodb.core.mixins import InimitableObject


class NotACursorMethod(Exception):
    pass


class DocumentSet(InimitableObject):
    def __init__(self, model, *args, **kwargs):
        self._model = model
        self.__cursor = Cursor(model.collection, *args, **kwargs)
    
    def __iter__(self):
        return self.__cursor
    
    def _model_representation(self, doc):
        m = deepcopy(self._model)
        m.set_model_data(doc)
        return m
    
    def next(self):
        return self._model_representation(next(self.__cursor))
    
    __next__ = next
    
    def first(self):
        doc = list(self.__cursor.clone().limit(-1))
        if not doc:
            return None
        m = self._model_representation(self.__cursor.limit(-1))
        return m
    
    def last(self):
        doc = list(self.__cursor.clone())[-1]
        if not doc:
            return None
        m = self._model_representation(doc)
        return m
    
    def limit(self, number):
        self.__cursor = self.__cursor.limit(number)
    
    def sort(self, key_or_list, direction=None):
        self.__cursor = self.__cursor.sort(key_or_list, direction)
    
    def count(self):
        return len(list(self.__cursor.clone()))
    
    def run_cursor_method(self, meth_name: str, *args, **kwargs):
        """Run a direct cursor method"""
        if meth_name.startswith('_'):
            raise NotACursorMethod('Cannot call attributes that start with _')
        
        meth = getattr(self.__cursor, meth_name, None)
        
        if meth is None:
            raise NotACursorMethod(f'Method `{meth_name} is not part of the Cursor class')
        if not callable(meth):
            raise NotACursorMethod(f'{meth_name} not a method of the Cursor class')
        if meth_name == 'clone':
            raise NotACursorMethod('Cannot run the clone method')
        
        obj = meth(*args, **kwargs)
        if isinstance(obj, Cursor):
            self.__cursor = obj
        else:
            return obj
