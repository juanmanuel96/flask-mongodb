from email.policy import default
import click
import flask.cli

from flask_mongodb.models.shitfs import Shift
from .utils import echo


@click.group('shift', help='Shift the database to make changes')
def db_shift():
    pass


@db_shift.command('history', help='Show all shift')
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--collection', '-c', help='Specify model collection name')
def show_shifts(database, collection):
    echo('shift history')


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
# @flask.cli.with_appcontext
def up(database, collection):
    echo('Shifting DB')
