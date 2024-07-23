import typing as t

from bson import ObjectId
from wtforms import StringField


class ObjectIdField(StringField):
    def process_data(self, value: t.Optional[ObjectId]):
        object_id = str(value) if isinstance(value, ObjectId) else value
        super().process_data(object_id)
