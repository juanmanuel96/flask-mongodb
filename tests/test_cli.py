from unittest import runner
import pytest

from flask import Flask
from click.testing import CliRunner

from flask_mongodb import MongoDB
# from flask_mongodb.cli.cli import cli
from flask_mongodb.cli.db_shifts import db_shift
from flask_mongodb.core.wrappers import MongoConnect
from tests.utils import DB_NAME, MAIN


NAME = DB_NAME + '_cli'
APP_CONFIG = {
    'TESTING': True,
    'DATABASE': {
        MAIN: {
            'HOST': 'localhost',
            'PORT': 27017,
            'NAME': NAME
        }
    },
    'MODELS': ['tests.model_for_tests.core']
}


@pytest.fixture(scope='function')
def app():
    _app = Flask(__name__)
    _app.config.update(APP_CONFIG)
    mongo = MongoDB(_app)
    
    yield _app
    
    client: MongoConnect = mongo.connections[MAIN].client
    client.drop_database(NAME)
    client.close()



def test_db_creation(app: Flask):
    runner = CliRunner()
    with app.app_context():
        result = runner.invoke(db_shift, ['start-db'])
        res = result.output.replace('\n', '') ==  'Database creation complete'
    assert res


def test_shift_history(app: Flask):
    runner = CliRunner()
    with app.app_context():
        result = runner.invoke(db_shift, ['examine'])
        res = result.exit_code == 0
    assert res

