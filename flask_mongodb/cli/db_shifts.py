from email.policy import default
import click
import flask.cli

from flask_mongodb.models.shitfs import Shift, create_db_shift_hisotry
from .utils import echo


@click.group('shift', help='Shift the database to make changes')
def db_shift():
    pass


@db_shift.command('history', help='Show the shift history')
@click.option('--database', '-d', default='main', help='Specify database')
@flask.cli.with_appcontext
def show_shifts(database):
    from flask_mongodb import current_mongo
    ShiftHistory = create_db_shift_hisotry(database)
    
    history = current_mongo.get_collection(ShiftHistory)
    data = history.manager.all()
    if len(data) < 1:
        echo('No history yet, execute the run command to make a history')
    else:
        for d in data:
            echo(f'{d.shifted.data} {d.collection.data}')


@db_shift.command('examine', help="Determine if must run a shift")
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
@flask.cli.with_appcontext
def examine(database, collection):
    from flask_mongodb import current_mongo
    
    models = current_mongo.collections[database]
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
        current_mongo._automatic_model_registration(current_app)
        
        for db_name in current_mongo.connections.keys():
            HistoryModel = create_db_shift_hisotry(db_name)
            current_mongo.register_collection(HistoryModel)
    else:
        # Check database is in the configurations
        if database not in current_app.config['DATABASE'].keys():
            echo('Database not in cofigurations, added it first before running this command')
            return  # exit
        
        if path and path not in current_app.config['MODELS']:
            current_app.config['MODELS'].clear()
            current_app.config['MODELS'].append(path)
            
        current_mongo._automatic_model_registration(current_app)
        
        if path:
            coll = path.split('.')[-1]
            if 'shift_history' not in current_mongo.collections[database][coll]:
            # Register DB shift history collection
                HistoryModel = create_db_shift_hisotry(database)
                current_mongo.register_collection(HistoryModel)
        else:
            for db_name in current_mongo.connections.keys():
                if 'shift_history' not in current_mongo.collections[db_name].keys():
                    HistoryModel = create_db_shift_hisotry(db_name)
                    current_mongo.register_collection(HistoryModel)
