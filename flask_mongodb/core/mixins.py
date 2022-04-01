import typing as t
from flask_mongodb.core.wrappers import MongoCollection


class ModelMixin:
    @property
    def model(self):
        return self._model
    
    @property
    def collection(self) -> MongoCollection:
        return self._model.collection
