from flask_mongodb import CollectionModel
from flask_mongodb.models import fields


class ModelForTest(CollectionModel):
    collection_name: str = 'shift_collection'

    sample_text = fields.StringField(required=True)
    sample_field = fields.BooleanField(default=False)  # Altered field
    sample_extra = fields.IntegerField(default=32)  # New field
