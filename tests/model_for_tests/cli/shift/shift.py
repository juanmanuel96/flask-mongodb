import datetime

from flask_mongodb import CollectionModel
from flask_mongodb.models import fields


class ModelForTest(CollectionModel):
    collection_name: str = 'shift_collection'

    sample_text = fields.StringField(required=True)
    # sample_embedded_doc = fields.EmbeddedDocumentField(
    #     properties={
    #         'field1': fields.BooleanField(),
    #         'field2': fields.DatetimeField(default=datetime.datetime.now)
    #     }
    # )
    sample_field = fields.BooleanField(default=False)
    sample_extra = fields.IntegerField(default=32)
