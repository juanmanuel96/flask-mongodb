import os.path

import pytest
from click.testing import CliRunner
from flask import Flask

from flask_mongodb import MongoDB, current_mongo
from flask_mongodb.cli.cli import create_model
from flask_mongodb.cli.db_shifts import db_shift
from flask_mongodb.core.exceptions import NoDatabaseShiftingRequired
from flask_mongodb.core.wrappers import MongoConnect
from flask_mongodb.models.shitfs.shift import Shift
from tests.model_for_tests.cli.shift.models import ModelForTest
from tests.model_for_tests.cli.shift.shift import ModelForTest as ShiftModel_T
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


def test_db_creation(app):
    runner = CliRunner()
    with app.app_context():
        result = runner.invoke(db_shift, ['start-db'])
        res = result.output.replace('\n', '') == 'Database creation complete'
    assert res


def test_shifting(app_for_shift):
    """
    This function will test the shifting process and examine at the same time since it is required to make a shift.
    :param app_for_shift:
    :return:
    """
    runner = CliRunner()

    with app_for_shift.app_context():
        runner.invoke(db_shift, ['start-db'])

        current_mongo.collections[ShiftModel_T.collection_name] = ShiftModel_T
        shift_history = current_mongo.collections[ShiftModel_T.db_alias]['shift_history']()

        # Have to call Shift class directly since in actual implementation requires modification of a file
        # and during execution of test, file changes are not captured real time
        shift = Shift(ShiftModel_T)
        try:
            shifted = shift.shift()
        except NoDatabaseShiftingRequired:
            # Ignore collections that do not need shifting
            pass

        if shifted:
            shift_history.manager.insert_one(
                db_collection=ShiftModel_T.collection_name,
                new_fields=shift.new_fields or None,
                removed_fields=shift.removed_fields or None,
                altered_fields=[shift.altered_fields] if shift.altered_fields else None
            )

        # Get the saved history to compare
        history = shift_history.manager.find_one(_id=shift_history.pk)

    assert history['db_collection'] == ShiftModel_T.collection_name, 'Shift was not achieved'


def test_no_shift_necessary(app_for_shift):
    runner = CliRunner()
    with app_for_shift.app_context():
        runner.invoke(db_shift, ['start-db'])

        # Have to call Shift class directly since in actual implementation requires modification of a file
        # and during execution of test, file changes are not captured real time
        with pytest.raises(NoDatabaseShiftingRequired):
            s = Shift(ModelForTest)
            s.shift()


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


def test_create_model():
    runner = CliRunner()
    runner.invoke(create_model)

    models_path = os.path.abspath(os.getcwd() + '/models.py')

    exists = os.path.exists(models_path)
    with open(models_path, 'r') as models_file:
        content_valid = 'CollectionModel' in models_file.read()

    os.remove(models_path)

    assert exists and content_valid


def test_check_history(app):
    runner = CliRunner()

    with app.app_context():
        runner.invoke(db_shift, ['start-db'])

        ShiftHistory = current_mongo.collections[ShiftModel_T.db_alias]['shift_history']

        for item in [
            {'name': 'collection1', 'new_fields': [], 'removed_fields': ['f1'], 'altered_fields': []},
            {'name': 'collection2', 'new_fields': ['f1'], 'removed_fields': [], 'altered_fields': ['f2']},
            {'name': 'collection3', 'new_fields': ['f2'], 'removed_fields': ['f4'], 'altered_fields': []}
        ]:
            ShiftHistory(
                db_collection=item['name'],
                new_fields=item['new_fields'] or None,
                removed_fields=item['removed_fields'] or None,
                altered_fields=item['altered_fields'] or None
            ).save()

        result = runner.invoke(db_shift, ['history'])
        res = ('collection3' in result.output
               and 'collection2' in result.output
               and ShiftHistory().manager.all().count() == 3
               )
    assert res
