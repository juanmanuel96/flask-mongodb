import typing as t

from flask_mongodb.core.exceptions import CollectionException, DatabaseException, InvalidClass, URIMissing
from flask_mongodb.core.wrappers import MongoConnect, MongoDatabase
from flask_mongodb.models import CollectionModel


class MongoDB(object):
    def __init__(self, app=None):
        """
        Connect your MongoDB client to a Flask application. The MongoFlask object
        has 3 attributes: client, db, and collection.
        1. `client` is the MongoDB instance in the computer.
        2. `db` is the Database to connect to.
        3. `collections` is a map of the CollectionModel objects

        NOTE: Only supports single database applications
        """
        self.__client = None  # MongoDB client
        self.__db = None  # Application database
        self.__collections = {}  # Database collections

        if app is not None:
            self.init_app(app)

    
    def init_app(self, app):
        host = app.config.get('MONGO_HOST')
        port = app.config.get('MONGO_PORT')
        db_name = app.config.get('MONGO_DATABASE')
        username = app.config.get('MONGO_USER')
        password = app.config.get('MONGO_PASSWORD')

        if not host or not port:
            raise URIMissing(f'MONGO_HOST and MONGO_PORT cannot be "{type(None)}"')

        if not db_name:
            raise DatabaseException()

        account = f'{username}:{password}@' if username and password else ''
        conn = f'{host}:{port}'
        uri = f'mongodb://{account}{conn}'

        self.__client = MongoConnect(uri)
        self.__database__(db_name)
        
        app.mongo = self

    @property
    def client(self):
        return self.__client

    @property
    def db(self):
        return self.__db

    @property
    def collections(self):
        return self.__collections

    def __str__(self) -> str:
        return str(self.collections)

    def __database__(self, db_name=None):
        """
        Sets the db attribute of the object.

        :param db_name: Name of the database to connect to
        :type db_name: str
        """
        if db_name is None:
            raise DatabaseException('Database must be provided')

        self.__db = MongoDatabase(self.client, db_name)

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
        _collection = collection_cls(self.db)
        self.__collections.update({name: _collection})
        return self.collections.get(name) is not None
    
    def get_collection(self, collection: t.Union[str, t.Type[CollectionModel]]) -> t.Type[CollectionModel]:
        """
        Retrieves a Collection instance from the collections attribute.

        :param collection_name: Name of the collection to be retrieved
        :type collection_name: str
        """
        try:
            collection_name = collection.collection_name
        except AttributeError:
            collection_name = collection.collection_name
        if not isinstance(collection_name, str):
            raise Exception('Must pass a collection or collection name')
        collection_to_return = self.collections.get(collection_name)
        if not collection_to_return:
            raise CollectionException('Collection invalid')
        return collection_to_return
    
    def session(self, causal_consistency=None, default_transaction_options=None, 
                snapshot=False):
        return self.client.start_session(causal_consistency=causal_consistency,
                                         default_transaction_options=default_transaction_options,
                                         snapshot=snapshot)
