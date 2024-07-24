import typing as t

from bson import ObjectId
from wtforms import form, validators

from flask_mongodb.forms.meta import CollectionModelFormMeta
from flask_mongodb.forms.fields import ObjectIdField
from flask_mongodb.models import CollectionModel


class CollectionModelForm(form.Form):
    Meta = CollectionModelFormMeta

    oid = ObjectIdField(default='')

    def __init__(self, formdata=None, obj=None, prefix="", data=None, meta=None,
                 instance: t.Optional[CollectionModel] = None,
                 **kwargs):
        super().__init__(formdata, obj, prefix, data, meta, **kwargs)

        self._validated = False
        self.instance = instance
        self._model: t.Type[CollectionModel] = self.meta.model

        if self.instance:
            for name, field in self.instance.fields.items():
                setattr(self, name, field.data)

    @property
    def data(self) -> t.Dict:
        d = super().data
        if 'oid' in d and d['oid']:
            d['_id'] = ObjectId(d.pop('oid'))  # Convert oid to _id which is required by the model
        return d

    def validate(self, extra_validators=None):
        validated = super().validate(extra_validators)
        if validated:
            self._validated = True
        return validated

    def save(self, session=None, bypass_validation=False, comment=None):
        if not self._validated:
            raise validators.ValidationError("Cannot save non-validated form")
        self.instance = self._model(**self.data)
        return self.instance.save(session, bypass_validation, comment)

    def delete(self, session=None, comment=None):
        if self.instance:
            # Will only delete if instance is given
            self.instance.delete(session, comment)
