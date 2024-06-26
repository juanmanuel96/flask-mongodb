import datetime

from flask_mongodb.models import CollectionModel, fields


def create_db_shift_history(db_name='main'):
    class ShiftHistory(CollectionModel):
        collection_name: str = 'shift_history'
        db_alias = db_name
        
        shifted = fields.DatetimeField(default=datetime.datetime.now)
        db_collection = fields.StringField()
        new_fields = fields.ArrayField(allow_null=True)
        removed_fields = fields.ArrayField(allow_null=True)
        altered_fields = fields.ArrayField(allow_null=True)
    return ShiftHistory
