# What are models?

Flask-MongoDB has a modelling class for your collections. The idea behind the models is somewhat the same as for the Django framework. The difference stands in the complexity behind the creation of these models compared to the ones of Django. Flask-MongoDB has a philosophy of making it easier for the developer to have their MongoDB collections well structured while still offering of having the data not so structured. 

A `CollectionModel` from Flask-MongoDB represents a collection of a particular database. It is composed of two components: metadata and fields. 

## The collection metadata

Its metadata are three class attributes: `collection_name`, `db_alias`, and `schemaless`. The former must be specified in all models while the last two have default values `main` and `False`. By default a collection belongs to the main database and applies schema validation at the DB level. The `schemaless` attribute is used to enable or disable schema validation, it does not remove the requirement of fields. Schema validation can be completely turned off from collection to collection, if the developer chooses so. 

## A collection's fields or schema

A model's fields are what define the schema of the collection. The schema of the collection are basically the keys most or all documents in the collection have. Fields by default will require some form of data. If the required flag is removed, it could be saved with a `None` value or some other default value. Future versions will include better methods for creating models where some can have very strict schemas while others have no schema at all, meaning the use of fields or dynamic assignments of fields. Currently, a model must have at least one field defined. 

# Creating a model

As explained in the previous section, the `MODELS` configuration searches for the models module inside the package path in the list. While this is not a requirement and you can use the `register_collection` method of the `MongoDB` class, the configuration method is the recommended option. This is because collection registration is done automatically by the package. 

## The CollectionModel

Inside a models module, you would need to create your model class which must inherit from the `CollectionModel` class of Flask-MongoDB.
```python
from flask_mongodb.models import CollectionModel

class BlogPost(CollectionModel):
    pass
```
In this example, the `BlogPost` model class is set to the DB of alias `main` and has schema validation enabled. However, this will not work since the `collection_name` attribute must be defined and at least one field is required. So, define the collection name. We will later define a field.
```python
from flask_mongodb.models import CollectionModel

class BlogPost(CollectionModel):
    collection_name = 'blog_post'
```

## Defining Fields

As mentioned above, the fields are why define the schema of a document in a collection (**Remember**: Collections in MongoDB are composed of documents where each document schema does not have to necessarilly match as the next one). Before we create a field in out example model, they must be explained first.

### Structure of fields

A field describes a key in a document. It has a BSON type, a required flag, allow null flag, a default value or callable, and a clean data function. The former is a class attribute while the rest are initialization parameters. The default value can be a constant value or a callable. 

There is a `Field` base class that all other field types inherit from. To create your own field type, you must inherit from this class and make sure the BSON type matches a MongoDB BSON type unless your field does not require it. A good example of a field type that does not require a BSON type is the `EnumField`. 

Each field, has its unique carachteristics. Some inherit from other field types, but do some special task or modification that justify its existance. For example, the `PasswordField` inherits from `StringField`. It modifies a bit the `set_data` method to hash the data that represents a password. 

Other characteristics are:

1. `required`: Makes the field require truthy value, default is `True`
2. `allow_null`: Permits data to be `None`, default is `False`
3. `default`: A default value the field will have; can be a callable
4. `clean_data_func`: A callable that will clean the data before it is returned

For more field specifics, refer to the API Reference section.

### Adding a field to the model

Now that fields have been explained, let's add a field to our model. Remember that at least one field is required for each model. To add a field, import the `fields` module from the `models` module.
```python
from flask_mongodb.models import CollectionModel, fields

class BlogPost(CollectionModel):
    collection_name = 'blog_post'
    
    title = fields.StringField(max_length=100)
    body = fields.StringField(min_length=25, max_length=1000)
```

This is all that is required to create a model. Add this model package to the `MODELS` config variable to register the collection.

# Making queries

MongoDB querying system uses JSON to make DB queries. Collection models come with a manager attribute which can run queries. The methods for running queries with the manager have the same name as the Collection instance from pymongo.

## Collection Manager

The `manager` attribute is an instance of the `CollectionManager` class. This class has a single attribute which is the model itself. The collection manager has the task of making every query to the database. As mentioned above, the manager implements the same querying as pymongo but modified to meet the requirements of Flask-MongoDB. The queries are:

- `find`: Returns a document set of copies of the model with the corresponding document values
- `find_one`: Returns a single model copy with the corresponding document values
- `insert_one`: Inserts one single document into the collection
- `update_one`: Updates only one document in the collection, default update type is `$set`
- `delete_one`: Deletes a single document in the collection

## Document Sets

The `DocumentSet` class is a list like class where it contains copies of the model with the corresponding values from the collection documents. Only the `find` function of the manager returns a document set. 
