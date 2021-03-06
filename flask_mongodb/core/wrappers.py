from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from flask_mongodb.core.mixins import InimitableObject


class MongoConnect(MongoClient, InimitableObject):
    """
    Wrapper from the pymongo.MongoClient class
    """
    def __getattr__(self, name):
        attr = super(MongoConnect, self).__getattr__(name)
        if isinstance(attr, Database):
            return MongoDatabase(self, name)
        return attr
    
    def __getitem__(self, item):
        attr = super(MongoConnect, self).__getitem__(item)
        if isinstance(attr, Database):
            return MongoDatabase(self, item)
        return attr


class MongoDatabase(Database, InimitableObject):
    """
    Wrapper for the pymongo.database.Database class
    """
    def __getattr__(self, name):  # noqa: D105
        attr = super(MongoDatabase, self).__getattr__(name)
        if isinstance(attr, Collection):
            return MongoCollection(self, name)
        return attr

    def __getitem__(self, item):  # noqa: D105
        item_ = super(MongoDatabase, self).__getitem__(item)
        if isinstance(item_, Collection):
            return MongoCollection(self, item)
        return item_


class MongoCollection(Collection, InimitableObject):
    """
    Wrapper class for the pymongo.collection.Collection class
    """
    def __getattr__(self, name):  # noqa: D105
        attr = super(MongoCollection, self).__getattr__(name)
        if isinstance(attr, Collection):
            db = self._Collection__database
            return MongoCollection(db, attr.name)
        return attr

    def __getitem__(self, item):  # noqa: D105
        item_ = super(MongoCollection, self).__getitem__(item)
        if isinstance(item_, Collection):
            db = self._Collection__database
            return MongoCollection(db, item_.name)
        return item_
