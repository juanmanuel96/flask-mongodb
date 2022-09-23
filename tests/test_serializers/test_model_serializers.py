import pytest
from wtforms import fields as wtfields 

from flask_mongodb.core import exceptions
from flask_mongodb.core.mongo import MongoDB
from flask_mongodb.serializers import ModelSerializer, fields, validators
from tests.fixtures import BaseAppSetup
from tests.model_for_tests.core.models import ModelForTest2


class SerializerForTest(ModelSerializer):
    serializer_model = ModelForTest2
    title = wtfields.StringField(validators=[validators.required(), validators.length(max=50)])
    body = wtfields.StringField(validators=[validators.required()])


DATA = {
    'title': 'Sample title',
    'body': 'Sample body'
    }


class TestModelSerializer(BaseAppSetup):
    MODELS = ['tests.model_for_tests.core']
    
    def test_serializer_is_valid(self):
        serializer = SerializerForTest(data=DATA)
        valid = serializer.is_valid()
        assert valid
    
    def test_very_long_title_error(self):
        data = DATA.copy()
        data.update(title='This is an extremely long title by the established standards of the model')
        serializer = SerializerForTest(data=data)
        
        with pytest.raises(exceptions.ValidationError):
            serializer.is_valid(raise_exception=True)
    
    def test_validated_data_before_is_valid(self):
        serializer = SerializerForTest(data=DATA)
        with pytest.raises(exceptions.ValidationError):
            serializer.validated_data
    
    def test_successful_insert_from_serializer(self):
        serializer = SerializerForTest(data=DATA)
        serializer.is_valid(raise_exception=True)
        serializer.model.set_model_data(serializer.validated_data)
        ack = serializer.manager.insert_one(serializer.model.data(include_reference=False))
        assert ack.acknowledged
    
    def test_sucessful_update_from_serializer(self, mongo: MongoDB):
        # First get the sample
        sample = mongo.get_collection(ModelForTest2).manager.find_one(title='Sample title')
        sample['body'] = 'This body has been updated'  # Change the body
        
        # Serialize, validate, and update
        serializer = SerializerForTest(data=sample.data(include_reference=False))
        valid = serializer.is_valid()
        ack = serializer.manager.update_one(query={'_id': sample.pk},
                                            update={'body': serializer.validated_data['body']})
        
        # Fecth the updated sample
        new_sample = mongo.get_collection(ModelForTest2).manager.find_one(_id=sample.pk)
        
        # Compare
        assert valid and ack.acknowledged and (new_sample['body'] == 'This body has been updated')
