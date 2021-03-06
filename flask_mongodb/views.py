import typing as t
from flask import current_app
from flask.views import MethodView
from flask_mongodb.core.exceptions import MissingViewModelException

from flask_mongodb.core.mongo import CollectionModel
from flask_mongodb.core.mixins import ModelMixin


class ModelView(MethodView, ModelMixin):
    view_model: t.Type[CollectionModel] = None

    def __init__(self):
        if self.view_model:
            assert issubclass(self.view_model, CollectionModel)
            self._model = current_app.mongo.get_collection(self.view_model)
        else:
            raise MissingViewModelException()
        super().__init__()

