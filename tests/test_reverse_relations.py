import pytest
from flask import Flask

from flask_mongodb.core.mongo import MongoDB
from tests.fixtures import BaseAppSetup
from tests.model_for_tests.reference.models import CarCompany, CarModel
from tests.utils import DB_NAME, MAIN


class TestReverseRelations(BaseAppSetup):
    APP_CONFIG = {
        'TESTING': True,
        'DATABASE': {
            MAIN: {
                'HOST': 'localhost',
                'PORT': 27017,
                'NAME': DB_NAME
            }
        },
        'MODELS': ['tests.model_for_tests.reference']
    }
    
    @pytest.fixture(scope='class', autouse=True)
    def setup_db(self, mongo: MongoDB):
        model = mongo.get_collection(CarCompany)
        model['company_name'] = 'GM'
        model['company_tax_id'] = '123'
        model['employees'] = 1500
        ack = model.manager.insert_one(model.data(include_reference=False))
        
        model = mongo.get_collection(CarModel)
        model['company'] = ack.inserted_id
        model['make'] = 'Chevrolet'
        model['car_model'] = 'Camaro'
        model['color'] = 'Black'
        model['year'] = 2019
        model.manager.insert_one(model.data(include_reference=False))
    
    def test_models_relation_attribute(self, application: Flask):
        model = application.mongo.get_collection(CarCompany)
        car_company = model.manager.find_one(company_name='GM')
        assert hasattr(car_company, 'car_models')