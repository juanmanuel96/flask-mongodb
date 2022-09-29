from email.policy import default
import click
import flask.cli

from .utils import echo


@click.group('shift', help='Shift the database to make changes')
def shift():
    pass


@shift.command('show', help='Show all shift')
@click.option('--database', '-d', default='main', help='Specify database')
@click.option('--model', help='Specify model')
def show_shifts(database):
    echo('showing')


@shift.command('create', help='Create a shift file')
@click.option('--model', '-m', help='Specify model to create shift file')
def create_shift_file(model):
    echo('Creating shift file')


@shift.command('up', help='Upshift the database')
@click.option('--database', '-d', default='main', help='Specify database')
# @flask.cli.with_appcontext
def up(database):
    echo('Shifting DB')


@shift.command('down', help='Downshift the database')
def down():
    echo('down')
