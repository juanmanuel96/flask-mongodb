import pytest

from flask_mongodb.core.mongo import MongoDB
from flask_mongodb.core import exceptions
from flask_mongodb.models.fields import ReferenceIdField
from tests.fixtures import BaseAppSetup
from tests.model_for_tests.reference.models import CarCompany, CarModel
from tests.utils import DB_NAME, MAIN


class TestReferenceAndReverseRelations(BaseAppSetup):
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
    
    @pytest.fixture(scope='class')
    def car_company(self, mongo: MongoDB) -> CarCompany:
        model = mongo.get_collection(CarCompany)
        car_company = model.manager.find_one(company_name='GM')
        return car_company
    
    @pytest.fixture(scope='class')
    def car_model(self, mongo: MongoDB) -> CarModel:
        model = mongo.get_collection(CarModel)
        car_model = model.manager.find_one(make='Chevrolet')
        return car_model
    
    # TESTS
    def test_reference(self, car_model: CarModel):
        company = car_model['company']
        assert isinstance(company, CarCompany)
    
    def test_reference_field(self, car_model: CarModel):
        company = car_model.company
        assert isinstance(company, ReferenceIdField)
    
    def test_models_relation_attribute(self, car_company: CarCompany):
        assert hasattr(car_company,  CarModel.company.related_name)
    
    def test_relation_finds_correct_data(self, car_company: CarCompany):
        car_model = car_company.car_models.find().first()
        assert car_model['car_model'] == 'Camaro'
    
    def test_insert_not_allowed(self, car_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            car_company.car_models.insert_one({})
    
    def test_insert_many_not_allowed(self, car_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            car_company.car_models.insert_many({})
    
    def test_update_one_not_allowed(self, car_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            car_company.car_models.update_one({}, {})
    
    def test_delete_one_not_allowed(self, car_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            car_company.car_models.delete_one({})
    
    def test_add_new_car_model(self, car_company: CarCompany, mongo: MongoDB):
        total_company_models = car_company.car_models.all().count()  # Should be 1
        car = mongo.get_collection(CarModel)
        car.set_model_data({'company': car_company.pk, 'make': 'Chevrolet', 'car_model': 'Corvette',
                              'color': 'red', 'year': 2022})
        car.manager.insert_one(car.data(include_reference=False))
        new_total = car_company.car_models.all().count()  # Should be 2
        assert new_total > total_company_models
