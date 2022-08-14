import pytest
from flask import Flask
from pymongo.errors import WriteError

from flask_mongodb import MongoDB, exceptions
from flask_mongodb.core.wrappers import MongoConnect
from flask_mongodb.models import CollectionModel
from flask_mongodb.models.document_set import DocumentSet

from tests.model_for_tests.core.models import ModelForTest, ModelForTest2
from tests.utils import DB_NAME, MAIN, remove_collections


class TestCollectionModels:
    APP_CONFIG = {
        'TESTING': True,
        'DATABASE': {
            MAIN: {
                'HOST': 'localhost',
                'PORT': 27017,
                'NAME': DB_NAME
            }
        }
    }

    @pytest.fixture(scope='class', autouse=True)
    def application(self):
        _app = Flask(__name__)
        _app.config.update(self.APP_CONFIG)
        _mongo = MongoDB(_app)
        
        yield _app
        
        client: MongoConnect = _mongo.connections[MAIN].client
        client.drop_database('flask_mongodb')
        client.close()
    
    @pytest.fixture(scope='class')
    def mongo(self, application: Flask):
        return application.mongo
    
    def test_auto_model_registration(self, application: Flask):
        application.config.update({'MODELS': ['tests.model_for_tests.core']})
        mongo = MongoDB(application)
        
        assert 'testing1' in mongo.connections[MAIN].list_collection_names(), \
            'Did not find expected collection name'
        
        remove_collections(mongo)

    def test_manual_model_registration(self, application: Flask):
        mongo = MongoDB(application)
        mongo.register_collection(ModelForTest)
        mongo.register_collection(ModelForTest2)
        
        assert 'testing2' in mongo.connections[MAIN].list_collection_names(), \
            'Did not find expected collection name'

    def test_record_creation(self, mongo: MongoDB):
        model = mongo.get_collection(ModelForTest)
        model['sample_text'] = 'This is just a sample text'
        ack = model.manager.insert_one(model.data(include_reference=False))
        
        assert ack, 'Insert was not successfull'

    def test_getting_data_from_db(self, mongo: MongoDB):
        model = mongo.get_collection(ModelForTest)
        ds = model.manager.find()
        
        assert isinstance(ds, DocumentSet), \
            'find() should return a DocumentSet'

    def test_document_set_elemets_are_models(self, mongo: MongoDB):
        model = mongo.get_collection(ModelForTest)
        ds = model.manager.find()
        
        assert all([isinstance(item, ModelForTest) for item in ds]), \
            'All instaces must be of the ModelForTest'

    def test_inimitable_object(self, mongo: MongoDB):
        model = mongo.get_collection(ModelForTest)
        instance: ModelForTest = model.manager.find().first()
        
        assert instance.collection is None, \
            "It seems that the collection was imitated"

    def test_required_field(self, mongo: MongoDB):
        model = mongo.get_collection(ModelForTest2)
        model['body'] = 'This is the body'
        
        with pytest.raises(WriteError):
            model.manager.insert_one(model.data(include_reference=False))

    def test_badly_configured_model(self, mongo: MongoDB):
        class BadlyConfiguredModel(CollectionModel):
            db_alias = None
            collection_name: str = 'bad'
        
        with pytest.raises(exceptions.CollectionException):
            mongo.register_collection(BadlyConfiguredModel)

    def test_unnamed_collection(self, mongo: MongoDB):
        class UnnamedCollection(CollectionModel):
            collection_name: str = None
        
        with pytest.raises(exceptions.CollectionException):
            mongo.register_collection(UnnamedCollection)