import click
import flask

from .utils import echo


@click.group('shift')
def shift():
    pass


@shift.command('up')
def up():
    click.echo('Shifting DB')


@shift.command('down')
def down():
    click.echo('down')
