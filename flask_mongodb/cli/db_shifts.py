import click
import flask.cli
import pymongo
from click import echo

from flask_mongodb.cli.utils import add_new_collection, create_collection, start_database, get_models_from_app
from flask_mongodb.core.exceptions import NoDatabaseShiftingRequired
from flask_mongodb.models.shitfs.history import create_db_shift_history
from flask_mongodb.models.shitfs.shift import Shift


@click.group('shift', help='Shift the database to make changes')
def db_shift():
    pass


@db_shift.command('history', help='Show the shift history')
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
@click.option('--order', '-o', default='asc', help='Ordering (default: asc)')
@flask.cli.with_appcontext
def show_shifts(database, collection, order):
    from flask_mongodb import current_mongo

    ordering = pymongo.ASCENDING if order == 'asc' else pymongo.DESCENDING

    ShiftHistory = current_mongo.collections[database]['shift_history']
    history = ShiftHistory()

    if collection:
        data = history.manager.filter(db_collection=collection).sort(('shifted', ordering))
    else:
        data = history.manager.all().sort(('shifted', ordering))

    if data.count() == 0:
        echo('No history yet, execute the run command to make a history')
    else:
        echo('History:')
        for d in data:
            echo(f'Collection: {d.db_collection.data} | Datetime: {d.shifted.data}')


@db_shift.command('examine', help="Determine if must run a shift")
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
@flask.cli.with_appcontext
def examine(database, collection):
    from flask import current_app

    # Get models from app and store in models_list
    models = get_models_from_app(current_app)
    examination = {}

    if collection and collection in models:
        # This will examine one collection
        model_class = models[collection]
        shift = Shift(model_class)
        examination[collection] = shift.examine()
    else:
        for name, model_class in models.items():
            shift = Shift(model_class)
            examination[name] = shift.examine()

    if any(list(examination.values())):
        echo(f'The following collections in {database} need shifting: ')
        for name, val in examination.items():
            if val:
                echo(name)
    else:
        echo('No shifting required')


@db_shift.command('run', help='Shift the database')
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
@flask.cli.with_appcontext
def run(database, collection):
    from flask import current_app
    from flask_mongodb import current_mongo

    models = get_models_from_app(current_app)
    ShiftHistory = current_mongo.collections[database]['shift_history']()

    if collection:
        models = {collection: models[collection]}

    shifted = False
    for m in models.values():
        shift = Shift(m)
        try:
            shifted = shift.shift()
        except NoDatabaseShiftingRequired:
            # Ignore collections that do not need shifting
            continue

        if shifted:
            ShiftHistory.manager.insert_one(
                db_collection=m.collection_name,
                new_fields=shift.new_fields or None,
                removed_fields=shift.removed_fields or None,
                altered_fields=[shift.altered_fields] if shift.altered_fields else None
            )

    if shifted:
        echo('Done shifting')
    else:
        echo('No shifting required')


@db_shift.command('start-db', help='Create new DB collections')
@click.option('--all', '-a', is_flag=True,
              help='Run in all databases, disables the database and path options')
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--path', '-p', help='Model path with dot notation')
@flask.cli.with_appcontext
def start(all, database: str, path: str):
    from flask import current_app
    from flask_mongodb import current_mongo

    if all:
        start_database(current_mongo, current_app)

        for db_name in current_mongo.connections.keys():
            HistoryModel = create_db_shift_history(db_name)
            create_collection(current_mongo, HistoryModel)
    else:
        # Check database is in the configurations
        if database not in current_app.config['DATABASE'].keys():
            echo('Database not in config, add it first before running this command')
            return  # exit

        if path and path not in current_app.config['MODELS']:
            current_app.config['MODELS'].clear()
            current_app.config['MODELS'].append(path)

        start_database(current_mongo, current_app, database)
        HistoryModel = create_db_shift_history(database)
        create_collection(current_mongo, HistoryModel)

    click.echo('Database creation complete')


@db_shift.command('add-collections', help='Add new collections to the database')
@click.option('--database', '-d', default='main', help='Database to run the addition on')
@flask.cli.with_appcontext
def add_collections(database):
    from flask import current_app
    from flask_mongodb import current_mongo

    try:
        db = current_mongo.connections[database]
    except KeyError:
        click.echo('Database does not exist')
        return

    if not db.client.list_database_names():
        click.echo('Run the start-db command first')
        return

    done = add_new_collection(current_mongo, current_app, database)
    click.echo('Addition of collection complete')

    return done
