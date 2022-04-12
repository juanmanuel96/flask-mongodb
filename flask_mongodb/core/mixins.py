import typing as t

from flask_mongodb.core.wrappers import MongoCollection


class ModelMixin:
    @property
    def model(self):
        from flask_mongodb.models import CollectionModel
        self._model: t.Type[CollectionModel]
        return self._model
    
    @property
    def collection(self) -> MongoCollection:
        return self._model.collection
