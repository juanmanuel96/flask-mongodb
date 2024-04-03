import logging
import typing as t

from flask import Flask
from pymongo.errors import ServerSelectionTimeoutError
from werkzeug.utils import import_string

from flask_mongodb.about import VERSION
from flask_mongodb.core.exceptions import (DatabaseAliasException, DatabaseException, ImproperConfiguration)
from flask_mongodb.core.wrappers import MongoConnect, MongoDatabase
from flask_mongodb.models import CollectionModel
from flask_mongodb.models.shitfs.history import create_db_shift_history

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class MongoDB:
    version = VERSION
    
    def __init__(self, app=None):
        """
        Connect your MongoDB client to a Flask application.
        """
        self.__connections: t.Dict[str, MongoDatabase] = {}
        self.__collections: t.Dict[str, t.Dict[str, t.Type[CollectionModel]]] = {}  # Database collections

        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        self._set_default_configurations(app)
        if not isinstance(app.config['DATABASE'], dict):
            raise TypeError('Database configuration must be a dictionary')
        
        database = app.config['DATABASE']
        if 'main' not in database:
            raise ImproperConfiguration('Must identify main database')
        
        for db_alias, db_details in database.items():
            assert isinstance(db_details, dict)
            host = db_details.get('HOST')
            port = db_details.get('PORT')
            username = db_details.get('USERNAME')
            password = db_details.get('PASSWORD')
            db_name = db_details.get('NAME')
            
            if not host or not port:
                raise ImproperConfiguration('HOST and PORT must be specified')

            if not db_name:
                raise ImproperConfiguration("Database name variable missing")
            
            account = f'{username}:{password}@' if username and password else ''
            conn = f'{host}:{port}'
            uri = f'mongodb://{account}{conn}'
            
            try:
                alias_client = MongoConnect(uri)
                alias_client.server_info()  # This is to test the connection
            except ServerSelectionTimeoutError:
                raise DatabaseException('No valid database connection established')
            
            db = MongoDatabase(alias_client, db_name)
            db.alias = db_alias
            self.__connections[db_alias] = db
        
        self._set_collections(app)
        
        app.mongo = self
    
    def __getitem__(self, arg) -> t.Union[MongoDatabase, None]:
        db = self.__connections.get(arg)
        if db is None:
            raise DatabaseAliasException('Invalid database name')
        return db
    
    def _set_default_configurations(self, app: Flask):
        db = {
            'main': {
                'HOST': 'localhost',
                'PORT': 27017,
                'NAME': 'main'
            }
        }
        app.config.setdefault('DATABASE', db)
        app.config.setdefault('MODELS', [])
    
    def _get_model_list(self, app: Flask) -> list:
        if not app.config['MODELS']:
            raise ImproperConfiguration('Need to list the model groups')
        models_list = []
        
        # Prepare a list of modules with their models
        for mod in app.config['MODELS']:
            mod = mod + '.models'
            models = import_string(mod)
            models_list.append(models)
        return models_list
    
    def _set_collections(self, app: Flask):
        models = self._get_model_list(app)
        for m in models:
            module_contents = dir(m)  # Get contents of the module
            for cont in module_contents:
                obj: t.Union[t.Type[CollectionModel], t.Any] = getattr(m, cont)  # Get each object
                
                # Register the obj as a collection if it has the collection_name
                # and db_alias attributes which all models should have
                if hasattr(obj, 'collection_name') and hasattr(obj, 'db_alias'):
                    if obj.collection_name is None:
                        # When the collection name is None, it is the base model class
                        continue
                    _name = obj.collection_name
                    # _instance = obj()
                    if obj.db_alias not in self.__collections:
                        self.__collections[obj.db_alias] = {}
                    # Initialize object to connect reference managers
                    self.__collections[obj.db_alias].update({_name: obj()})
        
        # Now add the history model
        for db in self.connections.keys():
            self.__collections[db].update(shift_history=create_db_shift_history(db))

    @property
    def collections(self):
        return self.__collections
    
    @property
    def connections(self):
        return self.__connections
    
    # TODO: Disabled
    # def session(self, causal_consistency=None, default_transaction_options=None, 
    #             snapshot=False, using='main'):
    #     return self.connections[using].client.start_session(causal_consistency=causal_consistency, 
    #                                                         default_transaction_options=default_transaction_options,
    #                                                         snapshot=snapshot)
    
    def disconnect(self, using='main'):
        return self.connections[using].client.close()
