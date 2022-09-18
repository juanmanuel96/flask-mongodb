import pytest
from flask_mongodb.core.mongo import MongoDB
from tests.fixtures import BaseAppSetup
from tests.model_for_tests.reference.models import CarCompany, CarModel


class TestReferencesSetUp(BaseAppSetup):
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
    
    @pytest.fixture(scope='class')
    def gm_company(self, mongo: MongoDB) -> CarCompany:
        model = mongo.get_collection(CarCompany)
        car_company = model.manager.find_one(company_name='GM')
        return car_company
    
    @pytest.fixture(scope='class')
    def car_model(self, mongo: MongoDB) -> CarModel:
        model = mongo.get_collection(CarModel)
        car_model = model.manager.find_one(make='Chevrolet')
        return car_model