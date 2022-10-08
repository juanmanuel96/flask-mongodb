import typing as t
import itertools as iter
from copy import deepcopy

from bson import ObjectId
from datetime import date, datetime
from werkzeug.security import generate_password_hash

from flask_mongodb.core.exceptions import FieldError, InvalidChoice


class FieldMixin:
    _model_field = True


class Field(FieldMixin):
    bson_type: list = None
    _validator_description = None

    def __init__(self, required: bool = True, allow_null=False, default: t.Union[t.Any, t.Callable]=None, 
                 clean_data_func=None) -> None:
        """
        Simple Field class for inheritance by other field types
        """
        if clean_data_func and not self._iscallable(clean_data_func):
            raise ValueError('`clean_data_func` must be callable')
        self.clean_data_func = clean_data_func
        self.required = required
        self.allow_null = allow_null
        self.__data__ = None
        self._validated = False
        
        if default:
            if self._iscallable(default):
                self.__data__ = default
            else:
                self.__data__ = self.validate_data(default) 

    @property
    def data(self) -> t.Any:
        if self._iscallable(self.__data__):
            return self.__data__()
        return self.get_data()

    @data.setter
    def data(self, value):
        self.run_validation(value)
        self.set_data(value)
    
    @property
    def description(self):
        return self._validator_description

    def _iscallable(self, value):
        return callable(value)
    
    def _check_if_allow_null(self, data):
        # To be called during data validation where is null is allowed and data is None,
        # the it should do nothing. Otherwise, should validate the data
        if self.allow_null and data is None:
            return True
        else:
            return False
    
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
    
    def set_data(self, value: t.Any) -> None:
        self.__data__ = value
    
    def get_data(self) -> t.Any:
        return self.__data__
    
    def run_validation(self, value):
        if not self._validated:
            self.validate_data(value)
    
    def validate_data(self, value):
        self._validated = True
        return value
    
    def clean_data(self):
        if self.clean_data_func:
            return self.clean_data_func(self.data)
        return self.data
    
    def clear(self):
        self.__data__ = None


class ObjectIdField(Field):
    bson_type = ["objectId"]
    
    def __init__(self, required: bool = True, allow_null=False, default=ObjectId) -> None:
        if issubclass(default, ObjectId):
            default = default()
        super().__init__(required, allow_null, default)
    
    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not any([
                isinstance(value, valid) for valid in [str, ObjectId]
                ]):
                raise TypeError("ObjectIDField data can only be "
                                "str or ObjectID")
        return super().validate_data(value)

    def set_data(self, value: t.Any) -> None:
        valid_data = self.validate_data(value)
        if isinstance(valid_data, str):
            # If it is a string, convert to ObjectId
            valid_data = ObjectId(valid_data)
        self.__data__ = valid_data


class StringField(Field):
    bson_type = ['string']

    def __init__(self, min_length=0, max_length=0, required=True, 
                 allow_null=False, default='', **kwargs) -> None:
        self.min_length = min_length
        self.max_length = max_length
        super(StringField, self).__init__(required, allow_null, default, **kwargs)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, str):
                raise TypeError(f'Incoming data must be string')
        return super().validate_data(value)


class PasswordField(StringField):
    def set_data(self, value: str):
        self.validate_data(value)
        if not value.startswith('pbkdf2:sha256:'):
            # Means the string is plain text and must be hashed
            self.__data__ = generate_password_hash(value)
        else:
            self.__data__ = value


class IntegerField(Field):
    bson_type = ['int']
    
    def __init__(self, required: bool = True, allow_null=False, default=0, **kwargs) -> None:
        super().__init__(required, allow_null, default, **kwargs)
    
    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if isinstance(value, str):
                value = int(value)
            if not isinstance(value, int):
                raise TypeError(f'Incoming data can only be integer')
        return super().validate_data(value)
 

class FloatField(Field):
    bson_type = ['double']
    
    def __init__(self, required: bool = True, allow_null=False, default=0.0, **kwargs) -> None:
        super().__init__(required, allow_null, default, **kwargs)
    
    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if isinstance(value, str):
                value = float(value)
            if not isinstance(value, float):
                raise TypeError(f'Incoming data can only be float')
        return super().validate_data(value)


class BooleanField(Field):
    bson_type = ['bool']

    def __init__(self, required=True, allow_null=False, default=False, **kwargs) -> None:
        super(BooleanField, self).__init__(required, allow_null, default, **kwargs)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, bool):
                raise TypeError(f'Incoming data must be boolean')
        return super().validate_data(value)


class DateField(Field):
    bson_type = ['date']
    
    def __init__(self, format='%Y-%m-%d', required: bool = True, allow_null=False, 
                 default: t.Union[datetime, date, None]=datetime(1901, 1, 1, 0, 0, 0, 0),
                 **kwargs) -> None:
        self.format = format
        super().__init__(required=required, allow_null=allow_null, default=default, **kwargs)
    
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
        


class DatetimeField(DateField):
    def __init__(self, required: bool = True, allow_null=False, 
                 default: t.Union[datetime, None] = datetime.now, **kwargs) -> None:
        super().__init__(format=None, required=required, allow_null=allow_null, default=default,
                         **kwargs)
    
    def set_data(self, value: t.Any) -> None:
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        to_data = self.validate_data(value, fmt)
        if isinstance(to_data, str):
            to_data = datetime.strptime(value, fmt)
        to_data = to_data if isinstance(to_data, datetime) or \
            self._check_if_allow_null(value) else \
                datetime(to_data.year, to_data.month, to_data.day)
        self.__data__ = to_data
    
    def strftime(self, fmt: str = None):
        fmt = self.format if not fmt else fmt
        return self.data.strftime(fmt)


class EmbeddedDocumentField(Field):
    bson_type = ['object']
    _validator_descriptor = 'Values must match the embedded document requirements'

    def __init__(self, properties: t.Dict = None, required=True,
                 allow_null=False, default: t.Union[t.Dict, t.Callable]={}, **kwargs) -> None:
        """
        data = {'field1': 'value1', 'field2': 'value2'}
        """
        if not properties or not isinstance(properties, dict):
            raise TypeError('properties param must be a dictionary')
        
        self.properties: t.Dict[str, Field] = self.__define_properties__(properties)
        if default:
            if self._iscallable(default):
                default = default()
            self._set_properties_data(default)
        super().__init__(required=required, allow_null=allow_null, default=default,
                         **kwargs)

    def __define_properties__(self, properties: t.Dict) -> t.Dict:
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
            value = data[prop_name]
            prop_field.data = value
    
    def get_data(self) -> t.Union[t.Dict, None]:
        if self._check_if_allow_null(self.__data__):
            return self.__data__
        json_field_data = {}
        for name, field in self.properties.items():
            json_field_data.update({name: field.data})
        self.__data__ = json_field_data
        return self.__data__
    
    def set_data(self, value: t.Union[dict, None]):
        self.validate_data(value)
        if self._check_if_allow_null(value):
            self.__data__ = value
        else:
            assert isinstance(value, dict)
            self._set_properties_data(value)
    
    def __iter__(self):
        return iter(self.data.keys() or [])


class ArrayField(Field):
    bson_type = ['array']
    
    def __init__(self, required: bool = True, min_items: int = -1, max_items=-1,
                 allow_null=False, default=[], **kwargs) -> None:
        if min_items > 0:
            self.min_items = min_items
        if max_items > 0:
            self.max_items = max_items
        super().__init__(required=required, allow_null=allow_null, default=default,
                         **kwargs)
    
    def validate_data(self, value):
        if self._check_if_allow_null(value):
            if not isinstance(value, list):
                raise TypeError(f'Incoming data can only be list')
        return super().validate_data(value)
    
    def __iter__(self):
        return iter(self.data or [])


class StructuredArrayField(ArrayField):
    _validator_descriptor = 'Items must match the desired structure'
    def __init__(self, items: dict[str, t.Type[Field]], required: bool = True, 
                 max_items: int = -1, min_items=-1, allow_null=False, default=[], 
                 unique_items=False, **kwargs) -> None:
        if not isinstance(items, dict):
            raise TypeError('items param must be dictionary')
        self.items = items
        self.unique_items = unique_items
        super().__init__(required, min_items, max_items, allow_null, default,
                         **kwargs)


class EnumField(Field):
    _validator_descriptor = 'Value must match the enum'
    bson_type = None
    
    def __init__(self, required: bool = True, 
                 choices: t.Tuple=None, allow_null=False, default='', 
                 expected_value_types=['string'], **kwargs) -> None:
        if not choices:
            raise FieldError('Must include choices')
        if not expected_value_types:
            raise FieldError('Must provide at leasr one expected value type as a BSON type alias')
        self.excpected_value_types = expected_value_types
        
        self.choices = choices
        self.enum = [choice[0] for choice in choices]
        super().__init__(required=required, allow_null=allow_null, default=default,
                         **kwargs)
    
    def validate_data(self, value):
        if self._check_if_allow_null(value):
            if (value not in self.enum):
                raise InvalidChoice("Not a valid choice")
        return super().validate_data(value)


class ReferenceIdField(Field):
    _reference = True
    bson_type = None
    _validator_description = 'Must be an objectId type'
    
    def __init__(self, model, required: bool = True, allow_null=False, default=None, 
                 clean_data_func=None, related_name=None, **kwargs) -> None:
        super().__init__(required, allow_null, default, clean_data_func, **kwargs)
        self.related_name = related_name if related_name else 'related'
        self.model = model
    
    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not any([
                isinstance(value, valid) for valid in [str, ObjectId]
                ]):
                raise TypeError("ObjectIDField data can only be "
                                "str or ObjectID")
        return super().validate_data(value)
    
    def get_data(self) -> t.Union[str, ObjectId]:
        return super().get_data()
    
    def set_data(self, value: t.Union[str, ObjectId]) -> None:
        valid_data = self.validate_data(value)
        if isinstance(valid_data, str):
            # If it's a string, convert to ObjectId
            valid_data = ObjectId(valid_data)
        self.__data__ = valid_data
    
    @property
    def reference(self):
        from flask_mongodb.globals import current_mongo
        reference_model = current_mongo.get_collection(self.model)
        ref = reference_model.manager.find_one(_id=self.data)
        return ref
