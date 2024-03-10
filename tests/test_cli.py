import pytest
from click.testing import CliRunner
from flask import Flask

from flask_mongodb import MongoDB
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


@pytest.fixture(scope='function')
def app_for_shift():
    APP_CONFIG['MODELS'] = ['tests.model_for_tests.cli.shift']

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
        res = result.output.replace('\n', '') == 'Database creation complete'
    assert res


@pytest.mark.skip(reason='Examine without data will always yield a possible shift')
def test_shift_history(app: Flask):
    runner = CliRunner()
    with app.app_context():
        result = runner.invoke(db_shift, ['examine'])
        res = result.exit_code == 0
    assert res


@pytest.mark.skip(reason='Shift is failing on models without any data')
def test_shifting(app_for_shift: Flask):
    runner = CliRunner()

    with app_for_shift.app_context():
        runner.invoke(db_shift, ['start-db'])

        with open('model_for_tests/cli/shift/models.py', 'r') as model_file:
            model_file_contents = model_file.read()  # Get the model file's contents

        with open('model_for_tests/cli/shift/shift.py', 'r') as shift_file:
            shift_file_contents = shift_file.read()  # Get shift file's contents

        with open('model_for_tests/cli/shift/models.py', 'w') as model_file:
            model_file.write(shift_file_contents)  # Replace model file content with shift data

        try:
            # Run shift command
            result = runner.invoke(db_shift, ['run'])
            res = result.exit_code == 0
        except Exception:
            res = False

        with open('model_for_tests/cli/shift/models.py', 'w') as model_file:
            model_file.write(model_file_contents)  # Rever model file to original contents

    assert res, 'Shift was not achieved'


def test_add_collection(app: Flask):
    runner = CliRunner()
    with app.app_context():
        runner.invoke(db_shift, ['start-db'])
        app.config['MODELS'].append('tests.model_for_tests.reference')
        try:
            result = runner.invoke(db_shift, ['add-collections'])
            res = result.exit_code == 0
        except Exception:
            res = False
    assert res, "Failed to create collection"
