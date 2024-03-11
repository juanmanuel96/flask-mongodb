import pytest
from flask import Flask

from flask_mongodb import MongoDB
from flask_mongodb.cli.utils import start_database
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
        },
        'MODELS': []
    }
    
    # All tests must specify the models that they will use
    MODELS = []
    
    @pytest.fixture(scope='class', autouse=True)
    def application(self):
        if not self.MODELS:
            # TODO: Create custom exception
            raise Exception('Missing models')
        
        self.APP_CONFIG.update(MODELS=self.MODELS)
        _app = Flask(__name__)
        _app.config.update(self.APP_CONFIG)
        _mongo = MongoDB()
        
        app_context = _app.app_context()
        app_context.push()

        _mongo.init_app(_app)
        start_database(_mongo, _app, 'main')
        
        yield _app
        
        app_context.pop()
        
        client: MongoConnect = _mongo.connections[MAIN].client
        client.drop_database(DB_NAME)
        client.close()
    
    @pytest.fixture(scope='class')
    def mongo(self, application: Flask):
        return application.mongo
