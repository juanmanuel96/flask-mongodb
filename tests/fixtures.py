from flask import Flask
import pytest

from flask_mongodb import MongoDB
from flask_mongodb.core.wrappers import MongoConnect
from tests.utils import DB_NAME, MAIN

class BaseAppSetup:
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
        
        app_context = _app.app_context()
        app_context.push()
        
        yield _app
        
        app_context.pop()
        
        client: MongoConnect = _mongo.connections[MAIN].client
        client.drop_database(DB_NAME)
        client.close()
    
    @pytest.fixture(scope='class')
    def mongo(self, application: Flask):
        return application.mongo