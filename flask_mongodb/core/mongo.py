import typing as t

from flask import Flask

from flask_mongodb.core.exceptions import DatabaseAliasException, DatabaseException, InvalidClass, URIMissing
from flask_mongodb.core.wrappers import MongoConnect, MongoDatabase
from flask_mongodb.models import CollectionModel


class MongoDB:
    def __init__(self, app=None):
        """
        Connect your MongoDB client to a Flask application.
        """
        self.__connections: t.Dict[str, MongoDatabase] = {}
        self.__collections: t.Dict[str, t.Dict[str, t.Type[CollectionModel]]] = {}  # Database collections

        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        if 'DATABASE' not in app.config:
            # TODO: Assign new exception
            raise Exception('Missing database configurations')
        if not isinstance(app.config['DATABASE'], dict):
            raise TypeError('Database configuration must be a dictionary')
        
        database = app.config['DATABASE']
        if 'main' not in database:
            # TODO: Assign new exception
            raise Exception('Must identify main database')
        
        for db_alias, db_details in app.config['DATABASE'].items():
            assert isinstance(db_details, dict)
            host = db_details.get('HOST')
            port = db_details.get('PORT')
            username = db_details.get('USERNAME')
            password = db_details.get('PASSWORD')
            db_name = db_details.get('NAME')
            
            if not host or not port:
                raise URIMissing('MONGO_HOST and MONGO_PORT must be specified')

            if not db_name:
                raise DatabaseException()
            
            account = f'{username}:{password}@' if username and password else ''
            conn = f'{host}:{port}'
            uri = f'mongodb://{account}{conn}'
            alias_client = MongoConnect(uri)
            db = MongoDatabase(alias_client, db_name)
            db.alias = db_alias
            self.__connections[db_alias] = db
        
        app.mongo = self

    @property
    def collections(self):
        return self.__collections
    
    @property
    def connections(self):
        return self.__connections
    
    def __getitem__(self, arg) -> t.Union[t.Type[MongoDatabase], None]:
        db = self.__connections.get(arg)
        if db is None:
            raise DatabaseAliasException('Invalid collection name')
        return db

    # def __iter__(self):
    #     return iter(self.__collections.values()

    def register_collection(self, collection_cls: t.Type[CollectionModel]):
        """
        Collection is a user-defined collection that will be added to the MongoFlask instance
        """
        if issubclass(collection_cls, CollectionModel):
            return self.__register_collection(collection_cls)
        else:
            raise InvalidClass('Invalid class type')

    def __register_collection(self, collection_cls: t.Type[CollectionModel]):
        _name = collection_cls.collection_name
        success = self._insert_collection(_name, collection_cls)
        if not success:
            raise Exception('Not success')
        return success

    def _insert_collection(self, name, collection_cls: t.Type[CollectionModel]) -> bool:
        """
        Inserts a new collection into the collections attribute.
        """
        _collection = collection_cls()
        _collection.connect(self.connections[_collection.db_alias])
        if _collection.db_alias not in self.__collections:
            self.__collections[_collection.db_alias] = {}
        self.__collections[_collection.db_alias].update({name: _collection})
        return True
    
    def get_collection(self, collection: t.Type[CollectionModel], default=None):
        """
        Retrieves a Collection instance from the collections attribute.

        :param collection_name: Name of the collection to be retrieved
        :type collection_name: str
        """
        collection_name = collection.collection_name
        if not isinstance(collection_name, str):
            raise Exception('Must pass a collection or collection name')
        try:
            collection_to_return = self.collections[collection.db_alias][collection_name]
            return collection_to_return
        except KeyError:
            return default
    
    def session(self, causal_consistency=None, default_transaction_options=None, 
                snapshot=False, using='main'):
        return self.connections[using].client.start_session(causal_consistency=causal_consistency, 
                                                            default_transaction_options=default_transaction_options,
                                                            snapshot=snapshot)
    
    def disconnect(self, using='main'):
        return self.connections[using].client.close()
