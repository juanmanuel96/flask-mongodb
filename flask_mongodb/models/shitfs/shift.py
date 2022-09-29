import typing as t

from flask_mongodb import current_mongo
from ..collection import CollectionModel


class Shift:
    def __init__(self, model: t.Type[CollectionModel]) -> None:
        self.movement = 'up'
        self._model = model
        self.collection_schema = None
    
    def switch_movement(self):
        if self.movement == 'up':
            self.movement = 'down'
        elif self.movement == 'down':
            self.movement = 'up'
        else:
            # Revert back to default state
            self.movement = 'up'
    
    def _up_shift(self):
        pass
    
    def _down_shift(self):
        pass
    
    def _get_collection_schema(self):
        database = current_mongo.connections[self._model.db_alias]
        collection = database.get_collection(self._model.collection_name)
        collection_options = collection.options()
        if collection_options:
            self.collection_schema = collection_options['validators']
    
    def _get_model_schema(self):
        return self._model.__define_validators__()


class ShiftFile:
    shift_class = Shift
    
    def construct_shift_file(self):
        pass
