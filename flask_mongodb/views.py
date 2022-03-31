import typing as t
from flask import request, current_app, Blueprint
from flask.views import MethodView
from flask_mongodb.core.exceptions import MissingViewModelException, NotABlueprintView

from flask_mongodb.core.mongo import CollectionModel
from flask_mongodb.core.mixins import ModelMixin


class ModelView(MethodView, ModelMixin):
    view_model = None

    def __init__(self):
        if self.view_model:
            assert issubclass(self.view_model, CollectionModel)
            self._model = current_app.mongo.get_collection(self.view_model.collection_name)
        else:
            raise MissingViewModelException()
        super().__init__()
    
    @property
    def blueprint(self) -> Blueprint:
        blueprint = request.blueprint
        if blueprint is None:
            raise NotABlueprintView()
        return current_app.blueprints[blueprint]

