import typing as t
from flask_mongodb.core.wrappers import MongoCollection
from flask_mongodb.models.collection import CollectionModel


class ModelMixin:
    @property
    def model(self) -> t.Type[CollectionModel]:
        return self._model
    
    @property
    def collection(self) -> MongoCollection:
        return self._model.collection
