from datetime import datetime

import pytest
from wtforms import fields as wtfields

from flask_mongodb.serializers import serializers, fields
from flask_mongodb.serializers import validators
from flask_mongodb.core.exceptions import ValidationError
from tests.fixtures import BaseAppSetup


class AddressSerializer(serializers.Serializer):
    line1 = wtfields.StringField(validators=[validators.required()])
    line2 = wtfields.StringField()
    city = wtfields.StringField(validators=[validators.required()])
    state = wtfields.StringField(validators=[validators.required()])
    country = wtfields.StringField(validators=[validators.required()])


class Serializer1(serializers.Serializer):
    first_name = wtfields.StringField(validators=[validators.required()])
    last_name = wtfields.StringField(validators=[validators.required()])
    address = fields.JSONField(AddressSerializer)
    created = wtfields.DateTimeField(validators=[validators.required()])


@pytest.mark.skip(reason='Serializers no longer supported, will be removed later')
class TestSerializer:
    def test_serializer_is_valid(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'address': {
                'line1': 'Carr. 1',
                'city': 'San Juan',
                'state': 'PR',
                'country': 'US'
            },
            'created': datetime.now()
        }
        serializer = Serializer1(data=data)
        valid = serializer.is_valid()
        assert valid
    
    def test_serializer_data_is_native(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'address': {
                'line1': 'Carr. 1',
                'city': 'San Juan',
                'state': 'PR',
                'country': 'US'
            },
            'created': datetime.now()
        }
        serializer = Serializer1(data=data)
        serializer.is_valid()
        assert isinstance(serializer.validated_data['created'], datetime)
    
    def test_serializer_raise_validation_error(self):
        data = {
            'first_name': '',
            'last_name': 'Doe',
            'address': {
                'line1': 'Carr. 1',
                'city': 'San Juan',
                'state': 'PR',
                'country': 'US'
            }
        }
        serializer = Serializer1(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
