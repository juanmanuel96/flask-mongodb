import typing as t
from copy import deepcopy

from pymongo.cursor import Cursor

from flask_mongodb.core.mixins import InimitableObject


class NotACursorMethod(Exception):
    pass


class DocumentSet(InimitableObject):
    def __init__(self, model, *args, **kwargs):
        from flask_mongodb.models import CollectionModel
        self._model: CollectionModel = model
        self.__cursor = Cursor(model.collection, *args, **kwargs)
    
    def __iter__(self):
        return self
    
    def _model_representation(self, doc):
        m = deepcopy(self._model)
        m.set_model_data(doc)
        m.connect()
        return m
    
    def next(self):
        return self._model_representation(next(self.__cursor))
    
    __next__ = next
    
    def first(self):
        doc = list(self.__cursor.clone().limit(-1))
        if not doc:
            return None
        m = self._model_representation(doc[0])
        return m
    
    def last(self):
        doc = list(self.__cursor.clone())
        if not doc:
            return None
        m = self._model_representation(doc[-1])
        return m
    
    def limit(self, number: int):
        """
        Limit the number of elements.
        :param number: Integer to limit the DocumentSet
        :return: Self
        """
        self.__cursor = self.__cursor.limit(number)
        return self
    
    def sort(self, sorting: t.Tuple[t.Tuple[str, int]]):
        """
        Sort the DocumentSet by the sorting list. The sorting param must be a tuple of tuples, where the first
        element is a field name and the second the sorting direction. For direction use :data:`pymongo.ASCENDING` or
        :data:`pymongo.DESCENDING`.
        :param sorting: Tuple of tuples of string and integer
        :return: Self
        """
        self.__cursor = self.__cursor.sort(key_or_list=sorting)
        return self
    
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
