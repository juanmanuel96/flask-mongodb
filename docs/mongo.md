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

It is recommended that in your configurations add a `DATABASE` variable to overwrite the default configurations and connect to your database. Remember that once you start the application, if the database does not exist it is created automatically. In your `DATABASE` variable, the first key is the database alias. It's value should be another dictionary with the following keys:

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

# Using the MongoDB instance at runtime

After you have registered the models and created your endpoints, you will most likely want to use the MongoDB instace through your application to make database operations. This section will explain how to get the MongoDB instance throughout your application.

## App context

When running a Flask application and importing certain modules or variables, it matters in which context you are making the call. There are proxies for the current application and request, for example. When you initialize the MongoDB object with the Flask instance, the Flask instance gets a new attribute called `mongo` which is the initialized MongoDB object. This creates two methods of importing the current MongoDB instance in the application context.

### Current App proxy

Using the `current_app` proxy, you can access the instanced MongoDB object through it by accessing the `mongo` attribute. With the `mongo` attribute you will have access to all of your MongoDB instance methods and attributes. 

```python
from flask import current_app

mongo_inst = current_app.mongo
```

### Current mongo proxy

Besides using the `current_app` proxy, you can use the `current_mongo` proxy. This proxy basically gets the `mongo` attribute from the current app and returns it. This makes the calls to the mongo instance to be shorter.

## Importing the MongoDB instance

In your app initialization file, you have to initialize your MongoDB instance after the Flask instance. After initialization, you can call the MongoDB instance directly like you would with the Flask instance. There is a caveat, though. This will not work with the app factory method or might raise import errors depending on how and where you make the import in your application. This methos is highly discouraged. 

# Using models at runtime

While developing your application, you will want to use the models. There are ways for you to get a model and use it during runtime. This section will explain all of the different methods for getting the models and using them.

## The `get_collection` method

The MongoDB class has a method called `get_collection` which is used to get a model registered model instance. This method has one required parameter. It must be the class type of the instance you wish to get. For example, let's say you have a `BlogPost` model and registered it automatically as explained above. To get the registered model instance, you would call the `get_collection` method from the MongoDB instance and pass the class `BlogPost` as parameters.

```python
from flask_mongodb import current_mongo
from ..blog.models import BlogPost

post_model = current_mongo.get_collection(BlogPost)
```

This will return the instance of `BlogPost` model which was registered automatically. Through it you can make queries, create collection documents, updating documents, etc.
