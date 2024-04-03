import click
import flask.cli
from click import echo
from werkzeug.utils import import_string

from flask_mongodb.models.shitfs.shift import Shift
from flask_mongodb.models.shitfs.history import create_db_shift_history
from flask_mongodb.cli.utils import add_new_collection, create_collection, start_database


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
    
    if data.count() == 0:
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
    examination = {}
    
    if collection:
        model = models[collection]
        shift = Shift(model)
        examination[collection] = shift.examine()
    else:
        for name, model in models.items():
            shift = Shift(model)
            examination[name] = shift.examine()
    
    if any(list(examination.values())):
        echo(f'The following collections in {database} need shifting: ')
        for name, val in examination.items():
            if val:
                echo(name)
    else:
        echo(f'No collection requires shifting in {database}')


@db_shift.command('run', help='Shift the database')
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
@flask.cli.with_appcontext
def run(database, collection):
    from flask import current_app
    from flask_mongodb import current_mongo

    models_path = current_app.config.get('MODELS', [])
    if not models_path:
        # TODO: Custom Exception
        raise Exception('missing models')
    models_list = []

    for mod in models_path:
        mod = mod + '.models'
        models = import_string(mod)
        models_list.append(models)

    models = {}

    for m in models_list:
        module_contents = dir(m)
        for cont in module_contents:
            obj = getattr(m, cont)
            if hasattr(obj, '_is_model'):
                collection_name = obj.collection_name
                if collection_name and obj.db_alias == database:
                    models[collection_name] = obj

    shift_history = current_mongo.collections[database]['shift_history']()
    
    if collection:
        models = {collection: models[collection]}
    
    for m in models.values():
        shift = Shift(m)
        shift.shift()
        shift_history.set_model_data({
            'db_collection': m.collection_name,
            'new_fields': shift.should_shift['new_fields'] or None,
            'removed_fields': shift.should_shift['removed_fields'] or None,
            'altered_fields': shift.should_shift['altered_fields'] or None
        })
        shift_history.save()
    
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
        start_database(current_mongo, current_app)
        
        for db_name in current_mongo.connections.keys():
            HistoryModel = create_db_shift_history(db_name)
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
