import pytest

from flask_mongodb.core.mongo import MongoDB
from tests.fixtures import BaseAppSetup
from tests.model_for_tests.reference.models import CarCompany, CarModel


class TestReferencesSetUp(BaseAppSetup):
    @pytest.fixture(scope='class', autouse=True)
    def setup_db(self, mongo: MongoDB):
        model = CarCompany(company_name='GM', company_tax_id='123', employees=1500)
        model.save()
        
        car_model = CarModel(company_id=model.pk, make='Chevrolet', car_model='Camaro', color='Black', year=2019)
        car_model.save()
    
    @pytest.fixture(scope='class')
    def gm_company(self, mongo: MongoDB) -> CarCompany:
        model = CarCompany()
        car_company = model.manager.find_one(company_name='GM')
        return car_company
    
    @pytest.fixture(scope='class')
    def car_model(self, mongo: MongoDB) -> CarModel:
        model = CarModel()
        car_model = model.manager.find_one(make='Chevrolet')
        return car_model
