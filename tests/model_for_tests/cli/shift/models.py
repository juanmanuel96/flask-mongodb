import datetime

from flask_mongodb import CollectionModel
from flask_mongodb.models import fields


class ModelForTest(CollectionModel):
    collection_name: str = 'shift_collection'

    sample_text = fields.StringField(required=True)
    sample_field = fields.DatetimeField(default=datetime.datetime.now)
    field_to_remove = fields.StringField(allow_null=True, default=None)
