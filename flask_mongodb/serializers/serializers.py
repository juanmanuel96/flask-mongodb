from flask import current_app
from flask_wtf import FlaskForm
from flask_mongodb.core.exceptions import ValidationError
from flask_mongodb.core.mixins import ModelMixin
from flask_mongodb.serializers.exceptions import MissingSerializerModel
from flask_mongodb.serializers.fields import JSONField


class Serializer(FlaskForm):
    __validated__ = False
    
    class Meta:
        csrf = False

    def __init__(self, **kwargs):
        if kwargs.get('meta'):
            _meta = kwargs.pop('meta')
            _meta['csrf'] = False  # Always disable CSRF
            kwargs.update(meta=_meta)
        self._validated_data = {}
        super().__init__(**kwargs)

    def is_valid(self, raise_exception=False):
        errors = {'errors': []}
        if not self.validate_on_submit():
            for name in self._fields:
                field = getattr(self, name, None)
                if field.errors:
                    errors['errors'] += [{name: err for err in field.errors}]
                    continue
                self._validated_data[name] = field.data
        if raise_exception and errors['errors']:
            raise ValidationError(message=errors)
        if errors['errors']:
            return errors
        else:
            self.__validated__ = True
            return self.__validated__

    @property
    def validated_data(self):
        if not self.__validated__:
            raise ValidationError('Run method `is_valid` first')
        _validated_data = {}
        for name in self._fields:
            field = getattr(self, name)
            if isinstance(field, JSONField):
                _validated_data[name] = {}
                for sub_field_name, sub_field in field.form_fields().items():
                    _validated_data[name][sub_field_name] = sub_field.data
            _validated_data[name] = field.data
        return _validated_data


class ModelSerializer(Serializer, ModelMixin):
    serializer_model = None

    def __init__(self, **kwargs):
        """
        The Model Serializer is just and extension of the Serializer by 
        connecting a model to the serializer.
        """
        if self.serializer_model:
            from flask_mongodb.models import CollectionModel
            assert issubclass(self.serializer_model, CollectionModel)
            self._model = current_app.mongo.get_collection(self.serializer_model.collection_name)
        else:
            raise MissingSerializerModel('Serializer Model must be specified')
        super().__init__(**kwargs)
