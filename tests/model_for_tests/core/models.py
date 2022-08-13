from flask_mongodb.models import CollectionModel, fields


class ModelForTest(CollectionModel):
    collection_name: str = 'testing1'
    sample_text = fields.StringField(required=True)


class ModelForTest2(CollectionModel):
    collection_name: str = 'testing2'
    title = fields.StringField(required=True, max_length=50)
    body = fields.StringField(required=True)
