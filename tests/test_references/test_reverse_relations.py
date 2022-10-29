import pytest

from flask_mongodb.core.mongo import MongoDB
from flask_mongodb.core import exceptions
from flask_mongodb.models.fields import ReferenceIdField
from tests.model_for_tests.reference.models import CarCompany, CarModel
from tests.test_references.base_setup import TestReferencesSetUp
from tests.utils import DB_NAME, MAIN


class TestReferenceAndReverseRelations(TestReferencesSetUp):
    MODELS = ['tests.model_for_tests.reference']
    
    # TESTS
    def test_models_relation_attribute(self, gm_company: CarCompany):
        assert hasattr(gm_company,  CarModel.company.related_name)
    
    def test_relation_finds_correct_data(self, gm_company: CarCompany):
        car_model = gm_company.car_models.find().first()
        assert car_model['car_model'] == 'Camaro'
    
    def test_insert_not_allowed(self, gm_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            gm_company.car_models.insert_one({})
    
    def test_insert_many_not_allowed(self, gm_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            gm_company.car_models.insert_many({})
    
    def test_update_one_not_allowed(self, gm_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            gm_company.car_models.update_one({}, {})
    
    def test_delete_one_not_allowed(self, gm_company: CarCompany):
        with pytest.raises(exceptions.OperationNotAllowed):
            gm_company.car_models.delete_one({})
    
    def test_add_new_car_model(self, gm_company: CarCompany, mongo: MongoDB):
        total_company_models = gm_company.car_models.all().count()  # Should be 1
        car = CarModel()
        car.set_model_data({'company': gm_company.pk, 'make': 'Chevrolet', 'car_model': 'Corvette',
                              'color': 'red', 'year': 2022})
        car.manager.insert_one(car.data(include_reference=False))
        new_total = gm_company.car_models.all().count()  # Should be 2
        assert new_total > total_company_models
