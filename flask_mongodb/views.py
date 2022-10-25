import typing as t
from flask.views import MethodView
from flask_mongodb.core.exceptions import MissingViewModelException

from flask_mongodb.core.mongo import CollectionModel


class ModelView(MethodView):
    view_model: t.Type[CollectionModel] = None

    def __init__(self):
        if self.view_model:
            assert issubclass(self.view_model, CollectionModel)
            self._model = self.view_model()
        else:
            raise MissingViewModelException()
        super().__init__()
    
    @property
    def model(self):
        return self._model

