import logging
import typing as t
from copy import deepcopy
from datetime import date, datetime

from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

from flask_mongodb.core.exceptions import FieldError, InvalidChoice

logger = logging.getLogger(__name__)


class emptyfield:  # type: ignore
    def set(self):
        pass

    def get(self):
        return None

    def __call__(self) -> t.Any:
        return self.get()


class FieldMixin:
    _model_field = True


class Field(FieldMixin):
    bson_type: t.List | None = None
    _validator_description = None

    def __init__(self, required: bool = True, allow_null=False,
                 default: t.Union[t.Any, t.Callable] = emptyfield(),
                 initial: t.Union[t.Any, t.Callable] = emptyfield(),
                 clean_data_func: t.Optional[t.Callable] = None) -> None:
        """
        Simple Field class for inheritance by other field types
        """
        if clean_data_func and not self._is_callable(clean_data_func):
            raise ValueError('`clean_data_func` must be callable')
        self.clean_data_func = clean_data_func if clean_data_func else self._clean_data_func
        self.required = required
        self.allow_null = allow_null
        self._validated = False
        self.__data__ = emptyfield()
        self._initial = emptyfield()

        if not isinstance(default, emptyfield):
            # If default is established then set to data and initial
            if self._is_callable(default):
                self.__data__ = default
                self._initial = default
            else:
                self.set_data(default)
                self.set_initial(default)

        if not isinstance(initial, emptyfield):
            # Overwrite the initial value if provided
            if self._is_callable(initial):
                self._initial = initial
            else:
                self.set_initial(initial)

    def __copy__(self):
        cls = self.__class__
        obj = cls.__new__(cls)
        obj.__dict__.update(self.__dict__)
        return obj

    def __deepcopy__(self, memo):
        cls = self.__class__
        obj = cls.__new__(cls)
        memo[id(self)] = obj
        for k, v in self.__dict__.items():
            setattr(obj, k, deepcopy(v, memo))
        return obj

    def _check_if_allow_null(self, data):
        # To be called during data validation where is null is allowed and data is None,
        # it should do nothing. Otherwise, should validate the data
        if self.allow_null and data is None:
            return True
        else:
            return False

    def _clean_data_func(self, data):
        return data

    @property
    def data(self) -> t.Any:
        if isinstance(self.__data__, emptyfield):
            return self.__data__.get()
        return self.clean_data_func(self.get_data())

    @property
    def initial(self):
        if isinstance(self._initial, emptyfield):
            return self._initial.get()
        return self.clean_data_func(self.get_initial())

    @property
    def description(self):
        return self._validator_description

    def set_data(self, value: t.Union[t.Callable, t.Any]) -> None:
        data = self.validate_data(value)
        self.__data__ = data

    def set_initial(self, value: t.Union[t.Callable, t.Any]) -> None:
        self._initial = value

    def get_data(self) -> t.Union[t.Callable, t.Any]:
        if self._is_callable(self.__data__):
            return self.__data__()
        return self.__data__

    def get_initial(self) -> t.Union[t.Callable, t.Any]:
        if self._is_callable(self._initial):
            return self._initial()
        return self._initial

    def run_validation(self, value):
        if not self._validated:
            self.validate_data(value)

    def validate_data(self, value):
        self._validated = True
        return value

    def clear(self):
        # Revert data and initial to emptyfield
        self.__data__ = emptyfield()
        self._initial = emptyfield()

    @staticmethod
    def _is_callable(value) -> bool:
        return callable(value)


class ObjectIdField(Field):
    bson_type = ["objectId"]

    def __init__(self, required: bool = True, allow_null=False, default=ObjectId) -> None:
        super().__init__(required, allow_null, default)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not any([
                isinstance(value, valid) or hasattr(value, '_is_model') for valid in [str, ObjectId]
            ]):
                raise TypeError("ObjectIDField data can only be "
                                "str, ObjectID, or a model")
        return super().validate_data(value)

    def set_data(self, value: t.Any) -> None:
        valid_data = self.validate_data(value)
        if isinstance(valid_data, str):
            # If it is a string, convert to ObjectId
            valid_data = ObjectId(valid_data)
        if hasattr(valid_data, '_is_model'):
            valid_data = valid_data.pk
        self.__data__ = valid_data


class StringField(Field):
    bson_type = ['string']

    def __init__(self, min_length=0, max_length=0, required=True,
                 allow_null=False, **kwargs) -> None:
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(required, allow_null, **kwargs)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, str):
                raise TypeError(f'Incoming data must be string')
        return super().validate_data(value)


class PasswordField(StringField):
    def set_data(self, value: str):
        value = self.validate_data(value)
        if not value.startswith('pbkdf2:sha256:'):
            # Means the string is plain text and must be hashed
            self.__data__ = generate_password_hash(value)
        else:
            self.__data__ = value

    def compare_password(self, password: str) -> bool:
        return check_password_hash(self.get_data(), password)


class IntegerField(Field):
    bson_type = ['int']

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if isinstance(value, str):
                value = int(value)
            if not isinstance(value, int):
                raise TypeError(f'Incoming data can only be integer')
        return super().validate_data(value)


class FloatField(Field):
    bson_type = ['double']

    def __init__(self, required: bool = True, allow_null=False, **kwargs) -> None:
        super().__init__(required, allow_null, **kwargs)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if isinstance(value, str):
                value = float(value)
            if not isinstance(value, float):
                raise TypeError(f'Incoming data can only be float')
        return super().validate_data(value)


class BooleanField(Field):
    bson_type = ['bool']

    def __init__(self, required=True, allow_null=False, **kwargs) -> None:
        super(BooleanField, self).__init__(required, allow_null, **kwargs)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, bool):
                raise TypeError(f'Incoming data must be boolean')
        return super().validate_data(value)


class DatetimeField(Field):
    bson_type = ['date']

    def __init__(self, required: bool = True, allow_null=False, date_format: str = "%Y-%m-%dT%H:%M:%S.%f",
                 **kwargs) -> None:
        super().__init__(required=required, allow_null=allow_null, **kwargs)
        self.format = date_format

    def validate_data(self, value: t.Union[str, datetime, date]):
        if not self._check_if_allow_null(value):
            if not any([isinstance(value, valid) for valid in [str, datetime, date]]):
                raise TypeError(f'Incoming data must be str, datetime, or date')
            if isinstance(value, str):
                # Will validate that the incoming value as string can return a valid datetime obj
                datetime.strptime(value, self.format)
        return super().validate_data(value)

    def set_data(self, value: t.Any) -> None:
        to_data = self.validate_data(value)
        if isinstance(to_data, str):
            to_data = datetime.strptime(value, self.format)
        to_data = to_data if (isinstance(to_data, datetime) or
                              self._check_if_allow_null(value)) else (
            datetime(to_data.year, to_data.month, to_data.day))
        self.__data__ = to_data

    def strftime(self, fmt: str = None):
        fmt = self.format if not fmt else fmt
        return self.data.strftime(fmt)


class DateField(DatetimeField):
    def __init__(self, required: bool = True, allow_null=False, date_format='%Y-%m-%d', **kwargs) -> None:
        super().__init__(required=required, allow_null=allow_null, date_format=date_format, **kwargs)

    def validate_data(self, value: t.Union[str, datetime, date], fmt: str = None):
        fmt = self.format if not fmt else fmt
        if not self._check_if_allow_null(value):
            if not any([isinstance(value, valid) for valid in [str, datetime, date]]):
                raise TypeError(f'Incoming data must be str, datetime, or date')
            if isinstance(value, str):
                # Will validate that the incoming value as srting can return a valid datetime obj
                datetime.strptime(value, fmt)
        return super().validate_data(value)

    def set_data(self, value: t.Any) -> None:
        to_data = self.validate_data(value)
        if isinstance(to_data, str):
            to_data = datetime.strptime(to_data, self.format)
        to_data = to_data if isinstance(to_data, datetime) or self._check_if_allow_null(value) \
            else datetime(to_data.year, to_data.month, to_data.day)
        self.__data__ = to_data

    @property
    def data(self) -> date:
        data = super().data
        return data.date()


class EmbeddedDocumentField(Field):
    bson_type = ['object']
    _validator_descriptor = 'Values must match the embedded document requirements'

    def __init__(self, properties: t.Dict = None, required=True,
                 allow_null=False, **kwargs) -> None:
        """
        data = {'field1': 'value1', 'field2': 'value2'}
        """
        if not properties or not isinstance(properties, dict):
            raise TypeError('properties param must be a dictionary')
        if allow_null:
            logger.warning('Setting allow_null=True will cause issues when saving, due to $jsonSchema properties.\n'
                           'It is recommended to always pass full document data.')

        self.properties: t.Dict[str, Field] = self._define_properties(properties)
        super().__init__(required=required, allow_null=allow_null, **kwargs)

    def __getitem__(self, __name: str):
        return self.data[__name]

    def _define_properties(self, properties: t.Dict) -> t.Dict:
        json_field_properties = {}
        for prop_name, prop in properties.items():
            # Validate correct property keys
            if not isinstance(prop_name, str):
                raise TypeError('Property names can only be of type string')
            if not issubclass(type(prop), Field):
                raise TypeError("Property must be a subclass of Field")
            if hasattr(prop, '_reference'):
                raise TypeError('Embedded field properties cannot have reference fields')
            json_field_properties[prop_name] = prop

        return json_field_properties

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, dict):
                raise TypeError(f'Incoming data must be dictionary')
        return super().validate_data(value)

    def _set_properties_data(self, data: dict):
        props = self.properties
        for prop_name, prop_field in props.items():
            value = data.get(prop_name, None)
            if value is not None:
                prop_field.set_data(value)

    def set_data(self, value: t.Union[dict, None]):
        value = self.validate_data(value)
        if value is None:
            self.__data__ = None
        else:
            self._set_properties_data(value)
            self.__data__ = self.properties

    def __iter__(self):
        return iter(self.data.keys() or [])


class ArrayField(Field):
    bson_type = ['array']

    def __init__(self, required: bool = True, min_items: int = -1, max_items=-1,
                 allow_null=False, **kwargs) -> None:
        if min_items > 0:
            self.min_items = min_items
        if max_items > 0:
            self.max_items = max_items
        super().__init__(required=required, allow_null=allow_null, **kwargs)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, list):
                raise TypeError(f'Incoming data can only be list')
        return super().validate_data(value)

    def __iter__(self):
        return iter(self.data or [])


class StructuredArrayField(ArrayField):
    _validator_descriptor = 'Items must match the desired structure'

    def __init__(self, items: dict[str, t.Type[Field]], required: bool = True,
                 max_items: int = -1, min_items=-1, allow_null=False,
                 unique_items=False, **kwargs) -> None:
        if not isinstance(items, dict):
            raise TypeError('items param must be dictionary')
        self.items = items
        self.unique_items = unique_items
        super().__init__(required, min_items, max_items, allow_null,
                         **kwargs)


class EnumField(Field):
    _validator_descriptor = 'Value must match the enum'
    bson_type = None

    def __init__(self, required: bool = True,
                 choices: t.Optional[t.Tuple] = None, allow_null=False,
                 expected_value_types=('string',), **kwargs) -> None:
        if not choices:
            raise FieldError('Must include choices')
        if not expected_value_types:
            raise FieldError('Must provide at least one expected value type as a BSON type alias')
        self.expected_value_types = expected_value_types

        self.choices = dict(choices)
        self.enum = [choice[0] for choice in choices]
        if allow_null:
            # If None is allowed, include it in the enum values
            self.enum.append(None)
        super().__init__(required=required, allow_null=allow_null, **kwargs)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if value not in self.enum:
                raise InvalidChoice("Not a valid choice")
        value = super().validate_data(value)
        return value.pk if hasattr(value, '_is_model') else value

    @property
    def verbose(self):
        return self.choices[self.data]


class ReferenceIdField(Field):
    _reference = True
    bson_type = ["objectId"]
    _validator_description = 'Must be an objectId type'

    def __init__(self, model, required: bool = True, allow_null=False,
                 clean_data_func=None, related_name=None, **kwargs) -> None:
        from flask_mongodb.models import CollectionModel

        super().__init__(required, allow_null, clean_data_func=clean_data_func, **kwargs)
        self.related_name = related_name
        self.model: t.Type[CollectionModel] = model

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not any([isinstance(value, (str, ObjectId)) or hasattr(value, '_is_model')]):
                raise TypeError("ObjectIDField data can only be str, ObjectID, or CollectionModel")
        return super().validate_data(value)

    def get_data(self) -> ObjectId:
        return super().get_data()

    def set_data(self, value) -> None:
        valid_data = self.validate_data(value)
        if isinstance(valid_data, str):
            # If it's a string, convert to ObjectId
            valid_data = ObjectId(valid_data)
        elif hasattr(valid_data, '_is_model'):
            valid_data = valid_data.pk

        self.__data__ = valid_data

    @property
    def reference(self):
        from flask_mongodb.models import CollectionModel

        if self.data is None:
            return None
        ref: CollectionModel = self.model().manager.find_one(_id=self.data)
        return ref
