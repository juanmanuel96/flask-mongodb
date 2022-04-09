from inspect import isclass
import typing as t
from wtforms.fields import Field
from wtforms.utils import unset_value
from flask_mongodb.serializers.exceptions import InvalidIncomingData


class JSONField(Field):
    widget = None
    
    def __init__(
        self, serializer_class, label=None, validators=None, separator="-", **kwargs
    ):
        from flask_mongodb.serializers import Serializer
        
        super().__init__(label, validators, **kwargs)
        assert issubclass(serializer_class, Serializer)
        self.serializer_class = serializer_class
        self.separator = separator
        self._obj = None
        if self.filters:
            raise TypeError(
                "FormField cannot take filters, as the encapsulated"
                " data is not mutable."
            )
        if validators:
            raise TypeError(
                "FormField does not accept any validators. Instead,"
                " define them on the enclosed form."
            )

    def process(self, formdata, data=unset_value, extra_filters=None):
        if extra_filters:
            raise TypeError(
                "FormField cannot take filters, as the encapsulated"
                "data is not mutable."
            )

        if data is unset_value:
            try:
                data = self.default()
            except TypeError:
                data = self.default
            self._obj = data

        self.object_data = data

        prefix = self.name + self.separator
        if isinstance(data, dict):
            self.form = self.serializer_class(formdata=None, prefix=prefix, data=data)
        else:
            raise InvalidIncomingData()

    def validate(self, form, extra_validators=()):
        if extra_validators:
            raise TypeError(
                "FormField does not accept in-line validators, as it"
                " gets errors from the enclosed form."
            )
        return self.form.validate()

    def populate_obj(self, obj, name):
        candidate = getattr(obj, name, None)
        if candidate is None:
            if self._obj is None:
                raise TypeError(
                    "populate_obj: cannot find a value to populate from"
                    " the provided obj or input data/defaults"
                )
            candidate = self._obj

        self.form.populate_obj(candidate)
        setattr(obj, name, candidate)

    def __iter__(self):
        return iter(self.form._fields)

    def __getitem__(self, name):
        return self.form[name]

    def __getattr__(self, name):
        return getattr(self.form, name)

    @property
    def data(self) -> dict:
        return self.form.validated_data

    @property
    def errors(self):
        return self.form.errors
    
    def form_fields(self) -> t.Dict:
        return self.form._fields
