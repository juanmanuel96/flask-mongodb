# Overview

Flask-MongoDB is a Flask extension for connecting one or more MongoDB connections to a Flask instance. This extension also includes collection modelling classes, model view, serializers, and model serializers.

# Installation

Currently, the package is not in pip. However, you can install the package with pip by pulling from GitHub with the follwing command: 
```
pip install -e git+https://github.com/juanmanuel96/flask-mongodb@v1.5.0#egg=flask_mongodb
```
If you wish to install a specific version, change the `@v1.5.0` by whichever you want or remove it entirely to pull the latest code from the `main` branch. 

# Quick Start

This quick start guide will help you set up a Flask application with Flask-MongoDB.

## Configuration

The first step is to set the Flask configurations. Flask-MongoDB only has two configurations: `DATABASE` and `MODELS`. The former tells the MongoDB instance to which databases to connect to while the latter tells the instance where the models are located. 

The `DATABASE` configuration must be a dictionary of dictionaries where the first level key is the database alias for the application and the value dictionary must have the host, port, database name, and username and password if it applies. You can connect as many databases as you want. They can even come from different hosts. Flask-MongoDB has default values for both configurations:
```python
# Database configuration
DATABASE = {
    'main': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'main'
    }
}

# Models configuration
MODELS = []
```
The `DATABASE` and `MODELS` configuration will be covered in more detail later in the documentation

## Connecting your database to Flask

Connecting you database to your Flask instance is the same as in any other Flask extension. First create your Flask instance. 
```python
from flask import Flask

app = Flask(__name__)
```
Import the `MongoDB` class and instanciate it.
```python
from flask import Flask
from flask_mongodb import MongoDB

app = Flask(__name__)
mongo = MongoDB()
```
To connect your MongoDB instance to the Flask instance, you have two options:

1. Pass the Flask instance as parameter of the `MongoDB` instanciation 
2. Use the factory method and call the `init_app` method from `MongoDB` passing a Flask instance as parameter.

Staring the application will automatically create the database and collections if necessary.