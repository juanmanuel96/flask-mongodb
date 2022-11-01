from email.policy import default
import click
import flask.cli

from flask_mongodb.models.shitfs import Shift, create_db_shift_hisotry
from .utils import create_collection, echo, start_database


@click.group('shift', help='Shift the database to make changes')
def db_shift():
    pass


@db_shift.command('history', help='Show the shift history')
@click.option('--database', '-d', default='main', help='Specify database')
@flask.cli.with_appcontext
def show_shifts(database):
    from flask_mongodb import current_mongo
    ShiftHistory = current_mongo.collections[database]['shift_history']
    history = ShiftHistory()
    data = history.manager.all()
    
    if data.count() < 1:
        echo('No history yet, execute the run command to make a history')
    else:
        for d in data:
            echo(f'{d.db_collection.data} {d.shifted.data}')


@db_shift.command('examine', help="Determine if must run a shift")
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
@flask.cli.with_appcontext
def examine(database, collection):
    from flask_mongodb import current_mongo
    
    models = current_mongo.collections[database]
    models.pop('shift_history', None)
    exmination = {}
    
    if collection:
        model = models[collection]
        shift = Shift(model)
        exmination[collection] = shift.examine()
    else:
        for name, model in models.items():
            shift = Shift(model)
            exmination[name] = shift.examine()
    
    if any(list(exmination.values())):
        echo(f'The following collections in {database} need shifting: ')
        for name, val in exmination.items():
            if val:
                echo(name)
    else:
        echo(f'No collection requires shifting in {database}')


@db_shift.command('run', help='Shift the database')
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
@flask.cli.with_appcontext
def run(database, collection):
    from flask_mongodb import current_mongo
    
    models = current_mongo.collections[database]
    
    shift_history = models.pop('shift_history')()
    
    if collection:
        models = {collection: models[collection]}
    
    for m in models.values():
        shift = Shift(m)
        shift.shift()
        shift_history.set_model_data(data={
            'db_collection': m.collection_name,
            'new_fields': shift.should_shift['new_fields'] or None,
            'removed_fields': shift.should_shift['removed_fields'] or None,
            'altered_fields': shift.should_shift['altered_fields'] or None
        })
        shift_history.manager.insert_one(shift_history.data(include_reference=False))
    
    echo('Done shifting')


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
        database, path = None, None
        start_database(current_mongo, current_app)
        
        for db_name in current_mongo.connections.keys():
            HistoryModel = create_db_shift_hisotry(db_name)
            create_collection(current_mongo, HistoryModel)
    else:
        # Check database is in the configurations
        if database not in current_app.config['DATABASE'].keys():
            echo('Database not in cofigurations, added it first before running this command')
            return  # exit
        
        if path and path not in current_app.config['MODELS']:
            current_app.config['MODELS'].clear()
            current_app.config['MODELS'].append(path)
            
        start_database(current_mongo, current_app, database)
        HistoryModel = create_db_shift_hisotry(database)
        create_collection(current_mongo, HistoryModel)
