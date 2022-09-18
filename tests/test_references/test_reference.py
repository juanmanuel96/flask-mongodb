from flask_mongodb import MongoDB
from tests.model_for_tests.reference.models import CarCompany, CarModel
from tests.test_references.base_setup import TestReferencesSetUp


class TestReferenceField(TestReferencesSetUp):
    MODELS = ['tests.model_for_tests.reference']
    
    #tests
    def test_create_car_compnay_and_car_model(self, mongo: MongoDB):
        car_company = mongo.get_collection(CarCompany)
        car_company.set_model_data({
            'company_name': 'Ford',
            'company_tax_id': '9865',
            'employees': 500
        })
        company_ack = car_company.manager.insert_one(car_company.data(include_reference=False))
        
        car_model = mongo.get_collection(CarModel)
        car_model.set_model_data({
            'company': company_ack.inserted_id,
            'make': 'Mustang',
            'car_model': 'GT500',
            'color': 'red',
            'year': 2020
        })
        car_ack = car_model.manager.insert_one(car_model.data(include_reference=False))
        
        assert company_ack.acknowledged and car_ack.acknowledged
    
    def test_update_one_by_reference(self, mongo: MongoDB):
        gm_company = mongo.get_collection(CarCompany).manager.find_one(company_name='GM')
        ford_company = mongo.get_collection(CarCompany).manager.find_one(company_name='Ford')
        
        new_car = mongo.get_collection(CarModel)
        new_car.set_model_data({
            'company': ford_company.pk,
            'make': 'Corvette',
            'car_model': 'C8',
            'color': 'white',
            'year': 2023
        })
        new_car.manager.insert_one(new_car.data(include_reference=False))
        
        # Now the update
        car_model = mongo.get_collection(CarModel).manager.find_one(make='Corvette')
        update = mongo.get_collection(CarModel).manager.update_one(query={'_id': car_model},
                                                                   update={'compnay': gm_company})
        
        assert update.acknowledged
    
    def test_delete_all_models_of_company(self, mongo: MongoDB, gm_company: CarCompany):
        delete = mongo.get_collection(CarModel).manager.delete_many(query={'company': gm_company})
        assert delete.acknowledged
