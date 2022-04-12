import typing as t
import itertools as iter

from bson import ObjectId
from datetime import date, datetime
from werkzeug.security import generate_password_hash

from flask_mongodb.core.exceptions import InvalidChoice


class Field:
    bson_type: str = None

    def __init__(self, required: bool = True, data: t.Any = None, allow_null=False, default=None) -> None:
        """
        Simple Field class for inheritance by other field types
        """
        self.required = required
        self.allow_null = allow_null
        self.__data__ = self.validate_data(data) if data else self.validate_data(default) 

    @property
    def data(self) -> t.Any:
        return self.__data__

    @data.setter
    def data(self, value):
        self.validate_data(value)
        self.__data__ = value

    def clean_data(self):
        return self.data

    def validate_data(self, value):
        return value
    
    def _check_if_allow_null(self, data):
        # To be called during data validation where is null is allowed and data is None,
        # the it should do nothing. Otherwise, should validate the data
        if self.allow_null and data is None:
            return True
        else:
            return False


class ObjectIDField(Field):
    bson_type = "objectId"
    
    def __init__(self, required: bool = True, data: t.Any = None, 
                 allow_null=False, default=ObjectId()) -> None:
        super().__init__(required, data, allow_null, default)
    
    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not any([
                isinstance(value, valid) for valid in [str, ObjectId]
                ]):
                raise TypeError("ObjectIDField data can only be "
                                "str or ObjectID")
        return super().validate_data(value)
    
    @property
    def data(self) -> t.Union[str, ObjectId]:
        return super().data
    
    @data.setter
    def data(self, value: t.Union[str, ObjectId]) -> None:
        valid_data = self.validate_data(value)
        if isinstance(valid_data, str):
            # If it is a string, convert to ObjectId
            valid_data = ObjectId(valid_data)
        self.__data__ = valid_data


class StringField(Field):
    bson_type = 'string'

    def __init__(self, min_length=0, max_length=0, required=True, data=None, allow_null=False, default='') -> None:
        self.min_length = min_length
        self.max_length = max_length
        super(StringField, self).__init__(required, data, allow_null, default)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, str):
                raise TypeError(f'Incoming data must be string')
        return super().validate_data(value)


class PasswordField(StringField):
    @property
    def data(self) -> str:
        return self.__data__
    
    @data.setter
    def data(self, value):
        self.validate_data(value)
        self.__data__ = generate_password_hash(value)


class IntegerField(Field):
    bson_type = 'int'
    
    def __init__(self, required: bool = True, data: t.Any = None, allow_null=False, default=0) -> None:
        super().__init__(required, data, allow_null, default)
    
    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if isinstance(value, str):
                value = int(value)
            if not isinstance(value, int):
                raise TypeError(f'Incoming data can only be integer')
        return super().validate_data(value)
 

class FloatField(Field):
    bson_type = 'double'
    
    def __init__(self, required: bool = True, data: t.Any = None, allow_null=False, default=0.0) -> None:
        super().__init__(required, data, allow_null, default)
    
    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if isinstance(value, str):
                value = float(value)
            if not isinstance(value, float):
                raise TypeError(f'Incoming data can only be float')
        return super().validate_data(value)


class BooleanField(Field):
    bson_type = 'bool'

    def __init__(self, required=True, data=None, allow_null=False, default=False) -> None:
        super(BooleanField, self).__init__(required, data, allow_null, default)

    def validate_data(self, value):
        if not self._check_if_allow_null(value):
            if not isinstance(value, bool):
                raise TypeError(f'Incoming data must be boolean')
        return super().validate_data(value)


class DateField(Field):
    bson_type = 'date'
    
    def __init__(self, format='%Y-%m-%d', required: bool = True, data: t.Union[str, datetime] = None,
                 allow_null=False, default: t.Union[datetime, date, None]=datetime(1901, 1, 1, 0, 0, 0, 0)) -> None:
        self.format = format
        super().__init__(required=required, data=data, allow_null=allow_null, default=default)
    
    def validate_data(self, value: t.Union[str, datetime, date], fmt: str = None):
        fmt = self.format if not fmt else fmt
        if not self._check_if_allow_null(value):
            if not any([isinstance(value, valid) for valid in [str, datetime, date]]):
                raise TypeError(f'Incoming data must be str, datetime, or date')
            if isinstance(value, str):
                # Will validate that the incoming value as srting can return a valid datetime obj
                datetime.strptime(value, fmt)
        return super().validate_data(value)
    
    @property
    def data(self) -> date:
        return self.__data__.date()
    
    @data.setter
    def data(self, value):
        to_data = self.validate_data(value)
        if isinstance(to_data, str):
            to_data = datetime.strptime(to_data, self.format)
        to_data = to_data if isinstance(to_data, datetime) else datetime(to_data.year, to_data.month, to_data.year)
        self.__data__ = to_data


class DatetimeField(DateField):
    def __init__(self, required: bool = True, data: t.Union[str, datetime] = None, allow_null=False, 
                 default: t.Union[datetime, None] = datetime.now()) -> None:
        super().__init__(format=None, required=required, data=data, allow_null=allow_null, default=default)
    
    @property
    def data(self) -> datetime:
        return self.__data__
    
    @data.setter
    def data(self, value: t.Union[str, datetime]):
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        to_data = self.validate_data(value, fmt)
        if isinstance(to_data, str):
            to_data = datetime.strptime(value, fmt)
        self.__data__ = to_data
    
    def strftime(self, fmt: str = None):
        fmt = self.format if not fmt else fmt
        return self.data.strftime(fmt)


class JsonField(Field):
    bson_type = 'object'

    def __init__(self, properties: t.Dict = None, required=True,
                 data: dict = None, allow_null=False, default={}) -> None:
        """
        data = {'field1': 'value1', 'field2': 'value2'}
        """
        if not properties or not isinstance(properties, dict):
            raise TypeError('properties param must be a dictionary')
        
        self.properties: t.Dict[str, Field] = self.__define_properties__(properties)
        if data:
            self._set_properties_data(data)
        super(JsonField, self).__init__(required=required, data=data, allow_null=allow_null, default=default)

    def __define_properties__(self, properties: t.Dict) -> t.Dict:
        json_field_properties = {}
        for prop_name, prop in properties.items():
            # Validate correct property keys
            if not isinstance(prop_name, str):
                raise TypeError('Property names can only be of type string')
            if not issubclass(type(prop), Field):
                raise TypeError("Property must be a subclass of Field")
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
    
    @property
    def data(self) -> t.Union[t.Dict, None]:
        if self._check_if_allow_null(self.__data__):
            return self.__data__
        json_field_data = {}
        for name, field in self.properties.items():
            json_field_data.update({name: field.data})
        self.__data__ = json_field_data
        return self.__data__
    
    @data.setter
    def data(self, value: t.Union[dict, None]):
        self.validate_data(value)
        if self._check_if_allow_null(value):
            self.__data__ = value
        else:
            assert isinstance(value, dict)
            self._set_properties_data(value)
    
    def __iter__(self):
        return iter(self.properties.keys())


class ArrayField(Field):
    bson_type = 'array'
    
    def __init__(self, required: bool = True, data: t.Any = None, max_items: int = -1, 
                 allow_null=False, default=[]) -> None:
        if max_items > 0:
            self.max_items = max_items
        super().__init__(required=required, data=data, allow_null=allow_null, default=default)
    
    def validate_data(self, value):
        if self._check_if_allow_null(value):
            if not isinstance(value, list):
                raise TypeError(f'Incoming data can only be list')
        return super().validate_data(value)
    
    def __iter__(self):
        return iter(self.data or [])


class SelectField(Field):
    bson_type = 'string'
    
    def __init__(self, required: bool = True, data: str = None, 
                 choices: t.Tuple=None, allow_null=False, default='') -> None:
        self.choices = choices
        self.enum = []
        for _, choice in self.choices:
            self.enum.append(choice)
        super().__init__(required=required, data=data, allow_null=allow_null, default=default)
    
    def validate_data(self, value):
        if self._check_if_allow_null(value):
            if not isinstance(value, str):
                raise TypeError(f'Incoming data must be string')
            if (value not in iter.chain(*self.choices)):
                raise InvalidChoice("Not a valid choice")
        return super().validate_data(value)
