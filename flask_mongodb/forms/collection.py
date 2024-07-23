import typing as t

from bson import ObjectId
from wtforms import form

from flask_mongodb.forms.meta import CollectionModelFormMeta
from flask_mongodb.forms.fields import ObjectIdField
from flask_mongodb.models import CollectionModel


class CollectionModelForm(form.Form):
    Meta = CollectionModelFormMeta

    oid = ObjectIdField(default='')

    def __init__(self, formdata=None, obj=None, data=None, meta=None, prefix="", **kwargs):
        self._validated = False
        self.instance: t.Optional[CollectionModel] = None
        super().__init__(formdata, obj, data, meta, prefix, **kwargs)
        self._model: t.Type[CollectionModel] = self.meta.model

    def validate(self, extra_validators=None):
        validated = super().validate(extra_validators)
        if validated:
            self._validated = True
        return validated

    @property
    def data(self) -> t.Dict:
        d = super().data
        if 'oid' in d and d['oid']:
            d['_id'] = ObjectId(d['oid'])  # Convert oid to _id which is required by the model
        return d

    def save(self, session=None, bypass_validation=False, comment=None):
        if not self._validated:
            # TODO: Create custom exception
            raise ValueError("Cannot save non-validated form")
        self.instance = self._model(**self.data).save(session, bypass_validation, comment)
