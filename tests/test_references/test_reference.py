from flask_mongodb import MongoDB
from flask_mongodb.models.fields import ReferenceIdField
from tests.model_for_tests.reference.models import CarCompany, CarModel
from tests.test_references.base_setup import TestReferencesSetUp


class TestReferenceField(TestReferencesSetUp):
    MODELS = ['tests.model_for_tests.reference']
    
    # Tests
    def test_reference(self, car_model: CarModel):
        company = car_model['company']
        assert isinstance(company, CarCompany)
    
    def test_reference_field(self, car_model: CarModel):
        company = car_model.company
        assert isinstance(company, ReferenceIdField)
    
    def test_create_car_company_and_car_model(self, mongo: MongoDB):
        car_company = CarCompany(company_name='Ford', company_tax_id='9865', employees=500)
        company_ack = car_company.save()
        
        car_model = CarModel(company=car_company, make='Mustang', car_model='GT500', color='red', year=2020)
        car_ack = car_model.save()
        
        assert company_ack.acknowledged and car_ack.acknowledged
    
    def test_update_one_by_reference(self, mongo: MongoDB):
        gm_company = CarCompany().manager.find_one(company_name='GM')
        ford_company = CarCompany().manager.find_one(company_name='Ford')
        
        new_car = CarModel(company=ford_company, make='Corvette', car_model='C8',
                           color='white', year=2023)
        new_car.save()
        
        # Now the update
        car_model = CarModel().manager.find_one(make='Corvette')
        car_model['company'] = gm_company
        update = car_model.save()
        
        assert update.acknowledged
    
    def test_delete_all_models_of_company(self, mongo: MongoDB, gm_company: CarCompany):
        delete = CarModel().manager.delete_many(query={'company': gm_company})
        assert delete.acknowledged
