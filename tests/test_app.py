import pytest
from flask import Flask

from flask_mongodb.core.exceptions import DatabaseException, ImproperConfiguration
from flask_mongodb.core.mongo import MongoDB
from flask_mongodb.core.wrappers import MongoConnect
from tests.utils import MAIN, DB_NAME

# TODO: These tests need to be updated or removed since the MODELS attribute is always required

@pytest.fixture(scope='module')
def app():
    _app = Flask(__name__)
    _app.config = {
        'TESTING': True,
        'DATABASE': {
            'main': {
                'HOST': 'localhost',
                'PORT': 27017,
                'NAME': DB_NAME
                }
            }
        }
    
    mongo = MongoDB(_app)
    
    yield _app
    
    client: MongoConnect = mongo.connections[MAIN].client
    client.drop_database(DB_NAME)
    client.close()


def test_mongo_connection_fails(app: Flask):
    config = {
        'DATABASE': {}
    }
    app.config.update(config)
    
    with pytest.raises(ImproperConfiguration()):
        MongoDB(app)


def test_mongo_connection_sucessful(app: Flask):
    if hasattr(app, 'mongo'):
        delattr(app, 'mongo')
    
    # Reconfigure for test
    config = {
        'DATABASE': {
            'main': {
                'HOST': 'localhost',
                'PORT': 27018,
                'NAME': DB_NAME
            }
        }
    }
    app.config.update(config)
    MongoDB(app)
    
    assert hasattr(app, 'mongo'), 'MongoDB connection failed'
