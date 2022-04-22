import typing as t


class ModelMixin:
    @property
    def model(self):
        from flask_mongodb.models import CollectionModel
        self._model: t.Type[CollectionModel]
        return self._model
