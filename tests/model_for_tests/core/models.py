from attr import field
from flask_mongodb.models import CollectionModel, fields


class ModelForTest(CollectionModel):
    collection_name: str = 'testing1'
    sample_text = fields.StringField(required=True)


class ModelForTest2(CollectionModel):
    collection_name: str = 'testing2'
    title = fields.StringField(required=True, max_length=50)
    body = fields.StringField(required=True)


class ModelWithEmbeddedDocument(CollectionModel):
    collection_name = 'embededded_document'
    
    phone_number = fields.EmbeddedDocumentField(
        properties={
            'number': fields.StringField(),
            'confirmed': fields.BooleanField(default=False),
            'confirmed_date': fields.DatetimeField(allow_null=True, default=None)
        }
    )
    first_name = fields.StringField()
    last_name = fields.StringField()
