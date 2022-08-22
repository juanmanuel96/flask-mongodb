# Understanding MongoDB

The main class of Flask-MongoDB is `MongoDB`. This class is the one that establishes the connection betweent he Flask app and the database. It is written the same way all Flask extensions write their code. The class has an optional app parameter and the `init_app` method. That method is the prefered way of creating the connection.

When a connection has been established, the Flask instance will have a new attribute called `mongo`. It can be accessed with the `current_app` proxy or the actual Flask instance.

# Configurations

The MongoDB class has two configuration variables. These are `DATABASE` and `MODELS`. The first one tells the MongoDB instance which databases and connections to use. The `MODELS` configuration allows for easier model registration. It tells the instance where to look for those models.

## Database settings

As mentioned before, the database configuration has default values. This default value connects the Flask app to a database of name main in localhost on port 27017, where the database alias is main.
```python
DATABASE = {
    'main': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'main'
    }
}
```
The `main` alias should always be present since by default all models are connected to main. However, it is up to you for setting the DB alias names. If `main` is not present, you must make sure that no model belongs to the `main` database. DB aliases on models will be covered later.

It is recommended that in your configurations add a `DATABASE` variable to overwrite the default configurations and connect to your database. Remember that once you start the application, if the database does not exist it is created automatically. In your `DATABASE` variable, the first key is the database alias. It's value should be another dictionary with the following keys: <br>

1. `HOST` - Host where the database is located (required)
2. `PORT` - Port of the database (required)
3. `NAME` - Name of the database in the connection (required)
4. `USERNAME` - Username of the account to be used to conduct the DB operations (optional)
5. `PASSWORD` - Password of the account (optional)

## Models configuration

The `MODELS` configuration provides an alternative for registering models to the MongoDB instance automatically and easily. Another way of registering models is by doing it manually with the `register_collection` method of the MongoDB class. While it is very similar to Flask's `register_blueprint` method, it is not scalable. That is where the `MODELS` variable come in to play. This variable must be a list of strings.

To register models automatically, simply add to the list the package path to the models. For exmaple, if you have a project with the following structure:
```
api
|__ __init__.py
|__ authentication
    |__ models
        |__ __init__.py
        |__ users.py
    |__ views
        |__ ...
|__ store
    |__ models
        |__ __init__.py
        |__ inventory.py
    |__ views
        |__ ...
app.py
```
You would want to register your authentication and store models automatically. In your configurations, create a new variable called MODELS. This variable must be a list. You should add `api.authentication` and `api.store` to the MODELS variable. Note that you do not add "models" to each of the package paths because the MongoDB instance will automatically search for `models` inside your packages. Your MODELS variable should look like this:
```python
MODELS = [
    'api.authentication',
    'api.store'
]
```
If you were to install other packages with Flask-MongoDB models, you would add the path to those models in the MODELS variable as well.
