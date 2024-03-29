import typing as t
import logging

from flask import Flask
from pymongo.errors import ServerSelectionTimeoutError
from werkzeug.utils import import_string

from flask_mongodb.about import VERSION
from flask_mongodb.core.exceptions import (CollectionInvalid, CouldNotRegisterCollection, 
                                           DatabaseAliasException, DatabaseException, ImproperConfiguration, InvalidClass)
from flask_mongodb.core.wrappers import MongoConnect, MongoDatabase
from flask_mongodb.models import CollectionModel
from flask_mongodb.models.shitfs.hisotry import create_db_shift_hisotry

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
                raise DatabaseException('No valid database connection estbalished')
            
            db = MongoDatabase(alias_client, db_name)
            db.alias = db_alias
            self.__connections[db_alias] = db
        
        self._set_collections(app)
        
        app.mongo = self
    
    def __getitem__(self, arg) -> t.Union[t.Type[MongoDatabase], None]:
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
    
    def _automatic_model_registration(self, app: Flask):
        """
        DEPRECATED: This method will be removed as of version 2
        """
        if not app.config['MODELS']:
            return None
        models_list = []
        
        # Prepare a list of modules with their models
        for mod in app.config['MODELS']:
            mod = mod + '.models'
            models = import_string(mod)
            models_list.append(models)
        
        # Itereate over the list and register the models
        for m in models_list:
            module_contents = dir(m)  # Get contents of the module
            for cont in module_contents:
                obj = getattr(m, cont)  # Get each object
                
                # Register the obj as a collection if it has the collection_name
                # and db_alias attributes which all models should have
                if hasattr(obj, 'collection_name') and hasattr(obj, 'db_alias'):
                    if obj.collection_name is None:
                        # When the collection name is None, it is the base model class
                        continue
                    self.__register_collection(obj)
    
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
            self.__collections[db].update(shift_history=create_db_shift_hisotry(db))
    
    def __register_collection(self, collection_cls: t.Type[CollectionModel]):
        """
        DEPRECATED: This method will be removed as of version 2
        """
        _name = collection_cls.collection_name
        success = self._insert_collection(_name, collection_cls)
        if not success:
            raise CouldNotRegisterCollection('Not success')
        return success
    
    def _insert_collection(self, name, collection_cls: t.Type[CollectionModel]) -> bool:
        """
        DEPRECATED: This method will be removed as of version 2
        
        Inserts a new collection into the collections attribute.
        """
        _collection = collection_cls()
        if _collection.db_alias not in self.__collections:
            self.__collections[_collection.db_alias] = {}
        self.__collections[_collection.db_alias].update({name: _collection})
        return True

    @property
    def collections(self):
        return self.__collections
    
    @property
    def connections(self):
        return self.__connections
    
    def register_models(self):
        logger.warning("DEPRECATED: register_models method is deprecated and will be " \
            "removed in version 2")
        from flask import current_app
        self._automatic_model_registration(current_app)

    def register_collection(self, collection_cls: t.Type[CollectionModel]):
        """
        DEPRECATED: This method will be removed as of version 2
        
        Collection is a user-defined collection that will be added to the MongoFlask instance
        """
        logger.warning('DEPRECATED: register_collection model is a deprecated method that will be '\
            'removed in version 2')
        
        if issubclass(collection_cls, CollectionModel):
            return self.__register_collection(collection_cls)
        else:
            raise InvalidClass('Invalid class type')
    
    def get_collection(self, collection: t.Type[CollectionModel], default=None):
        """
        DEPRECATED: This method will be removed as of version 2
        Retrieves a Collection instance from the collections attribute.

        :param collection_name: Name of the collection to be retrieved
        :type collection_name: str
        """
        logger.warning('register_collection model is a deprecated method that will be '\
            'removed in version 2')
        
        collection_name = collection.collection_name
        if not isinstance(collection_name, str):
            raise CollectionInvalid('Must pass a collection or collection name')
        try:
            collection_to_return = self.collections[collection.db_alias][collection_name]
            return collection_to_return
        except KeyError:
            return default
    
    # TODO: Disabled
    # def session(self, causal_consistency=None, default_transaction_options=None, 
    #             snapshot=False, using='main'):
    #     return self.connections[using].client.start_session(causal_consistency=causal_consistency, 
    #                                                         default_transaction_options=default_transaction_options,
    #                                                         snapshot=snapshot)
    
    def disconnect(self, using='main'):
        return self.connections[using].client.close()
