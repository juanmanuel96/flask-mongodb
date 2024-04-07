# What are models?

Flask-MongoDB has a modelling class for your collections. The idea behind the models is somewhat the same as for the Django framework. The difference stands in the complexity behind the creation of these models compared to the ones of Django. Flask-MongoDB has a philosophy of making it easier for the developer to have their MongoDB collections well-structured while still offering of having the data not so structured. 

A `CollectionModel` from Flask-MongoDB represents a collection of a particular database. It is composed of metadata, fields, and the manager. 

## The collection metadata

Its metadata are three class attributes: `collection_name`, `db_alias`, and `schemaless`. The first one must be specified in all models while the last two have default values `main` and `False`. By default, a collection belongs to the main database and applies schema validation at the DB level. The `schemaless` attribute is used to enable or disable schema validation, it does not remove the requirement of fields. Schema validation can be completely turned off from collection to collection, if the developer chooses so. 

## A collection's fields or schema

A model's fields are what define the schema of the collection. The schema of the collection are basically the keys most or all documents in the collection have. Fields by default will require some form of data. If the required flag is removed, it could be saved with a `None` value or some other default value. Future versions will include better methods for creating models where some can have very strict schemas while others have no schema at all, meaning the use of fields or dynamic assignments of fields. Currently, a model must have at least one field defined. 

## Creating a model

As explained in the previous section, the `MODELS` configuration searches for the models module inside the package path in the list. This configuration is a list of packages or locations where a `models.py` file or `models` package exists.

### The CollectionModel

Inside a model's module, you would need to create your model class which must inherit from the `CollectionModel` class of Flask-MongoDB.
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

### Defining model fields

As mentioned above, the fields are what define the schema of a document in a collection. Before we create a field in our example model, they must be explained first.

#### Structure of fields

A field describes a key in a document. It has a BSON type, a required flag, allow null flag, a default value or callable, an initial value or callable, and a clean data function. 

The fields have their unique characteristics. Some inherit from other field types, but do some special task or modification that justify its existence. For example, the `PasswordField` inherits from `StringField`. It modifies a bit the `set_data` method to hash the data that represents a password. 

Other characteristics are:

1. `required`: Makes the field require truthy value, default is `True`
2. `allow_null`: Permits data to be `None`, default is `False`
3. `default`: A default value the field will have; can be a callable.
4. `initial`: An initial value for the field; can be a callable.
5. `clean_data_func`: A callable that will clean the data before it is returned.

For more field specifics, refer to the API Reference section.

#### Adding a field to the model

Now that fields have been explained, let's add a field to our model. Remember that at least one field is required for each model. To add a field, import the `fields` module from the `models` module.
```python
from flask_mongodb.models import CollectionModel, fields

class BlogPost(CollectionModel):
    collection_name = 'blog_post'
    
    title = fields.StringField(max_length=100)
    body = fields.StringField(min_length=25, max_length=1000)
```

This is all that is required to create a model.

### The save method

The CollectionModel class has a save method that will take care of inserting and updating the collection document. When you instantiate a CollectionModel, the `_id` field data is set to None by default. Executing the `save` method will evaluate the `_id` field. If it is `None`, then it will run an insert action and update the instance's `_id` field with the new ObjectId value. Otherwise, an `update_one` operation will be done. Note that the update type is a `$set`. The method will return the pymongo operation result.

### The delete method

The CollectionModel class also has a delete method that will take care of deleting the current instance document representation. It will run the collection operation of delete on based on the `_id` of the document. The method will return the pymongo operation result. 

## Making queries

MongoDB querying system uses JSON to make DB queries. Collection models instances come with a manager attribute which can run queries. The methods for running queries with the manager have the same name as the Collection instance from pymongo.

### Collection Manager

The `manager` attribute is an instance of the `CollectionManager` class. The collection manager has the task of making every query to the database. As mentioned above, the manager implements the same querying as pymongo but modified to meet the requirements of Flask-MongoDB. 

Queries can be divided into two groups: reads and writes.

#### Read queries

- `find`: Returns a document set of copies of the model with the corresponding document values
- `find_one`: Returns a single model copy with the corresponding document values

#### Write Queries

- `insert_one`: Inserts one single document into the collection and returns a representation of the model
- `update_one`: Updates only one document in the collection. Default update type is `$set`. Returns a representation of the model
- `delete_one`: Deletes a single document in the collection, returns the pymongo result
- `delete_many`: Deletes all documents that match the query, returns the pymongo result.

### ReferenceManager

The ReferenceManager class is another manager, but for reverse references. A reverse reference is when Model A references Model B, with the reference manager Model B will have access to Model A data after instantiating the model. This manager only supports the `find` and `find_one` query methods.

### Document Sets

The `DocumentSet` class is a list like class where it contains copies of the model with the corresponding values from the collection documents. Only the `find` and `all` functions of the manager return DocumentSet instances. The DocumentSet instance has a `Cursor` object that is the query result. Iterating through the DocumentSet will return the model representation of the current document in its model form.

#### DocumentSet methods

The DocumentSet has many custom methods and wraps many of the Cursor class methods.

##### first method

The `first` method returns the first document of the query result.

##### last method

Just like the `first` method returns the first document of the query result, the `last` method returns the last one.

##### limit method

The `limit` method limits the cursor to the first n documents. Returns self for chaining DocumentSet methods.

##### sort method

The `sort` method sorts the cursor by the provided keys and directions. Returns self for chaining DocumentSet methods.

##### count method

The `count` method returns an int representation of the total count of documents of the cursor.

##### run_cursor_method

This method allows the developer to manually run methods of the `Cursor` class on the DocumentSet instance which have not been defined for the DocumentSet.
