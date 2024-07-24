import typing as t

from wtforms.meta import DefaultMeta

from flask_mongodb.models import CollectionModel


class CollectionModelFormMeta(DefaultMeta):
    model: t.Type[CollectionModel] = None

    # -- CSRF
    _csrf = False
    _csrf_field_name = "modelform_csrf"
    _csrf_secret = None
    _csrf_context = None
    _csrf_class = None

    def __init__(self) -> None:
        if self.model is None:
            raise AttributeError("model must be set on the Meta class")
    
    @property
    def csrf(self):
        return self._csrf
    
    @property
    def csrf_field_name(self):
        return self._csrf_field_name
    
    @property
    def csrf_secret(self):
        return self._csrf_secret
    
    @property
    def csrf_context(self):
        return self._csrf_context
    
    @property
    def csrf_class(self):
        return self._csrf_class
