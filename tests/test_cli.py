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


def test_db_creation():
    app = Flask(__name__)
    app.config.update(APP_CONFIG)
    mongo = MongoDB(app)
    runner = CliRunner()
    
    with app.app_context():
        result = runner.invoke(db_shift, ['start-db'])
        res = result.output.replace('\n', '') ==  'Database creation complete'
    
    client: MongoConnect = mongo.connections[MAIN].client
    client.drop_database(NAME)
    client.close()
    
    assert res


def test_shift_history():
    pass

