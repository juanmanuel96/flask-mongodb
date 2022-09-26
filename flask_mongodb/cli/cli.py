import os

import click

from flask_mongodb.core.mongo import MongoDB
from .db_shifts import shift
from .utils import echo


@click.group('flask-mongodb', help=f"The Flask MongoDB CLI tool. Version: v{MongoDB.version}")
def cli(version):
    pass


def show_version(ctx, param ,value):
    if not value:
        return
    
    echo(f'Version: v{MongoDB.version}')
    ctx.exit()


version_options = click.Option(
    ['--version'],
    is_flag=True,
    callback=show_version,
    help='Show package version'
)


@cli.command('create-model')
@click.option('--path', default='.', help='Path for the model file')
@click.option('--package', default=None, help='Place model in package')
def create_model(path, package):
    click.echo('Creating model...')
    
    base_path = os.path.abspath(os.getcwd())
    if path != '.':
        if not os.path.isdir(os.path.join(base_path, path)):
            os.mkdir(os.path.join(base_path, path))
    else:
        path = ''
    path = os.path.join(base_path, path)
    
    if package:
        path = os.path.abspath(os.path.join(path, package))
        os.mkdir(path)
        with open(os.path.join(path, '__init__.py'), 'w'):
            pass
        with open(os.path.join(path, 'models.py'), 'w') as models_file:
            models_file.write("from flask_mongodb import CollectionModel \n\n"\
                              "# Create you model here\n")
    else:
        with open(os.path.join(path, 'models.py'), 'w') as models_file:
            models_file.write("from flask_mongodb import CollectionModel \n\n"\
                              "# Create you model here\n")
    echo(path)


cli.add_command(shift)


if __name__ == '__main__':
    cli.params.append(version_options)
    cli()
