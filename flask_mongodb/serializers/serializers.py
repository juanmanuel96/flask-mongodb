import typing as t
import itertools

from flask import current_app
from wtforms.form import BaseForm, FormMeta
from wtforms.fields import Field

from flask_mongodb.core.exceptions import ValidationError
from flask_mongodb.core.mixins import ModelMixin
from flask_mongodb.models.collection import CollectionModel
from flask_mongodb.serializers.exceptions import MissingSerializerModel
from flask_mongodb.serializers.fields import JSONField
from flask_mongodb.serializers.meta import SerializerMeta


_default_serializer_meta = SerializerMeta

class SerializerBase(BaseForm):
    def __init__(self, fields: dict, prefix="", meta=_default_serializer_meta):
        """
        :param fields:
            A dict or sequence of 2-tuples of partially-constructed fields.
        :param prefix:
            If provided, all fields will have their name prefixed with the
            value.
        :param meta:
            A meta instance which is used for configuration and customization
            of WTForms behaviors.
        """
        if prefix and prefix[-1] not in "-_;:/.":
            prefix += "-"

        self.meta = meta
        self._prefix = prefix
        self._fields = dict()
        self._csrf_token_field = None

        if hasattr(fields, "items"):
            fields = fields.items()

        translations = self.meta.get_translations(self)
        if meta.csrf:
            self._csrf = meta.build_csrf(self)
            self._csrf_token_field = self._csrf.setup_form(self)

        for name, unbound_field in itertools.chain(fields):
            field_name = unbound_field.name or name
            options = dict(name=field_name, prefix=prefix, translations=translations)
            field = meta.bind_field(self, unbound_field, options)
            self._fields[name] = field

        self.form_errors = []
    
    def __setitem__(self, name: str, value):
        assert issubclass(type(value), Field)
        return super().__setitem__(name, value)
    
    @property
    def csrf_token_field(self):
        if self._csrf_token_field is None:
            raise NotImplementedError('CSRF Token field is called but not created')
        return self._csrf_token_field

class Serializer(SerializerBase, metaclass=FormMeta):
    __validated__ = False
    
    Meta = SerializerMeta

    def __init__(self, data=None, formdata=None, obj=None, prefix="", meta=None, **kwargs):
        """
        :param data: Take existing data from keys in this dict matching
            form field attributes. ``obj`` takes precedence if it also
            has a matching attribute. Only used if ``formdata`` is not
            passed.
        :param formdata: Input data coming from the client, usually
            ``request.form`` or equivalent. Should provide a "multi
            dict" interface to get a list of values for a given key,
            such as what Werkzeug, Django, and WebOb provide.
        :param obj: Take existing data from attributes on this object
            matching form field attributes. Only used if ``formdata`` is
            not passed.
        :param prefix: If provided, all fields will have their name
            prefixed with the value. This is for distinguishing multiple
            forms on a single page. This only affects the HTML name for
            matching input data, not the Python name for matching
            existing data.
        :param meta: A dict of attributes to override on this form's
            :attr:`meta` instance.
        :param extra_filters: A dict mapping field attribute names to
            lists of extra filter functions to run. Extra filters run
            after filters passed when creating the field. If the form
            has ``filter_<fieldname>``, it is the last extra filter.
        :param kwargs: Merged with ``data`` to allow passing existing
            data as parameters. Overwrites any duplicate keys in
            ``data``. Only used if ``formdata`` is not passed.
        """
        if formdata and data:
            raise ValueError('Only data or formdata can be passed, not both')
        self._validated_data = {}
        
        meta_obj = self._wtforms_meta()
        if meta is not None and isinstance(meta, dict):
            meta_obj.update_values(meta)
        super().__init__(self._unbound_fields, meta=meta_obj, prefix=prefix)

        for name, field in self._fields.items():
            # Set all the fields to attributes so that they obscure the class
            # attributes with the same names.
            setattr(self, name, field)
        self.process(formdata, obj, data=data, **kwargs)

    def is_valid(self, raise_exception=False):
        errors = {'errors': []}
        if not self.validate():
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
        # _validated_data = {}
        # for name in self._fields:
        #     field = getattr(self, name)
        #     if isinstance(field, JSONField):
        #         _validated_data[name] = {}
        #         for sub_field_name, sub_field in field.data.items():
        #             _validated_data[name][sub_field_name] = sub_field.data
        #     _validated_data[name] = field.data
        # return _validated_data
        return self._validated_data
    
    @property
    def data(self):
        raise NotImplementedError('Use the prefered property: `validated_data`')

    def __delitem__(self, name):
        del self._fields[name]
        setattr(self, name, None)

    def __delattr__(self, name):
        if name in self._fields:
            self.__delitem__(name)
        else:
            # This is done for idempotency, if we have a name which is a field,
            # we want to mask it by setting the value to None.
            unbound_field = getattr(self.__class__, name, None)
            if unbound_field is not None and hasattr(unbound_field, "_formfield"):
                setattr(self, name, None)
            else:
                super().__delattr__(name)

    def validate(self, extra_validators=None):
        """Validate the form by calling ``validate`` on each field.
        Returns ``True`` if validation passes.

        If the form defines a ``validate_<fieldname>`` method, it is
        appended as an extra validator for the field's ``validate``.

        :param extra_validators: A dict mapping field names to lists of
            extra validator methods to run. Extra validators run after
            validators passed when creating the field. If the form has
            ``validate_<fieldname>``, it is the last extra validator.
        """
        if extra_validators is not None:
            extra = extra_validators.copy()
        else:
            extra = {}

        for name in self._fields:
            inline = getattr(self.__class__, f"validate_{name}", None)
            if inline is not None:
                extra.setdefault(name, []).append(inline)

        return super().validate(extra)


class ModelSerializer(Serializer, ModelMixin):
    serializer_model: t.Type[CollectionModel] = None

    def __init__(self, **kwargs):
        """
        The Model Serializer is just and extension of the Serializer by 
        connecting a model to the serializer.
        """
        if self.serializer_model:
            from flask_mongodb.models import CollectionModel
            assert issubclass(self.serializer_model, CollectionModel)
            self._model = current_app.mongo.get_collection(self.serializer_model)
        else:
            raise MissingSerializerModel('Serializer Model must be specified')
        super().__init__(**kwargs)
