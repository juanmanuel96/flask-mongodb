# The MongoDB Class

The main class of Flask-MongoDB is `MongoDB`. This class is the one that establishes the connection betweent he Flask app and the database. It is written the same way all Flask extensions write their code. The class has an optional app parameter and the `init_app` method. That method is the prefered way of creating the connection.

When a connection has been established, the Flask instance will have a new attribute called `mongo`. It can be accessed with the `current_app` proxy or the actual Flask instance.

## Configurations

The MongoDB class has two configuration variables. These are `DATABASE` and `MODELS`. The first one tells the MongoDB instance which databases and connections to use. The `MODELS` configuration tells the instance where to look for those models. The elements of the list are refered to as model groups.

### Database settings

As mentioned above, the database configuration has default values. This default value connects the Flask app to a database of name main in localhost on port 27017, where the database alias is main.

**Structure**
```python
DATABASE = {
    'DB alias': {
        'HOST': 'host of the database',
        'PORT': 'port of the database',
        'NAME': 'name of the database'
    }
}
```

**Example**
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

It is recommended that in your configurations add a `DATABASE` variable to overwrite the default configurations and connect to your database. Remember that once you start the application, if the database does not exist it is created automatically. In your `DATABASE` variable, the first key is the database alias. Its value should be another dictionary with the following keys:

1. `HOST` - Host where the database is located (required)
2. `PORT` - Port of the database (required)
3. `NAME` - Name of the database in the connection (required)
4. `USERNAME` - Username of the account to be used to conduct the DB operations (optional)
5. `PASSWORD` - Password of the account, required if username is used (optional)

These DB configurations needs to be repeated for all databases you wish to connect to the application. Make sure not to repeat aliases.

### Models configuration

The `MODELS` configuration provides is the main method for registering models to the MongoDB instance automatically and easily. To register models automatically, simply add to the list the package path to the models. For exmaple, if you have a project with the following structure:

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
```

You would want to register your authentication and store models automatically. In your configurations, create a new variable called MODELS. This variable must be a list. You should add `api.authentication` and `api.store` to the MODELS variable. Note that you do not add "models" to each of the package paths because the MongoDB instance will automatically search for `models` inside your packages. Your `MODELS` variable should look like this:

```python
MODELS = [
    'api.authentication',
    'api.store'
]
```

If you were to install other packages with Flask-MongoDB models, you would add the path to those models in the `MODELS` configuration as well. The models file can be treated as package or as a simple file with all of the models in it.

## Using the MongoDB instance at runtime

After you have registered the models and created your endpoints, you will most likely want to use the MongoDB instace through your application to make database operations. This section will explain how to get the MongoDB instance throughout your application.

### App context

When running a Flask application and importing certain modules or variables, it matters in which context you are making the call. There are proxies for the current application and request, for example. When you initialize the MongoDB object with the Flask instance, the Flask instance gets a new attribute called `mongo` which is the initialized MongoDB object. This creates two methods of importing the current MongoDB instance in the application context.

#### Current App proxy

Using the `current_app` proxy, you can access the instanced MongoDB object through it by accessing the `mongo` attribute. With the `mongo` attribute you will have access to all of your MongoDB instance methods and attributes. 

```python
from flask import current_app

mongo = current_app.mongo
```

#### Current mongo proxy

Besides using the `current_app` proxy, you can use the `current_mongo` proxy. This proxy basically gets the `mongo` attribute from the current app and returns it. This makes the calls to the mongo instance to be shorter.

### Importing the MongoDB instance

In your app initialization file, you have to initialize your MongoDB instance after the Flask instance. After initialization, you can call the MongoDB instance directly like you would with the Flask instance. There is a caveat, though. This will not work with the app factory method or might raise import errors depending on how and where you make the import in your application. This method is highly discouraged.

## Using models at runtime

While developing your application, you will want to use the models. You can import any of your models as you would import any other class in Python. To use the model, simply initialize it and you can do model oprations with it. 
