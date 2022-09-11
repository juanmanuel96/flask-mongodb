from flask_mongodb.models import CollectionModel, fields


class CarCompany(CollectionModel):
    collection_name: str = 'car_companies'
    
    company_name = fields.StringField()
    company_tax_id = fields.StringField()
    employees = fields.IntegerField()


class CarModel(CollectionModel):
    collection_name: str = 'car_model'
    
    company = fields.ReferenceIdField(CarCompany, related_name='car_models')
    make = fields.StringField()
    car_model = fields.StringField()
    color = fields.StringField()
    year = fields.IntegerField()
