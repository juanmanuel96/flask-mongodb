# API Reference

This part of the documentation covers all of the interfaces Flask-MongoDB has to offer. 

## The MongoDB object

_class_ <span class='py_class'>flask_mongodb.MongoDB</span>(_app=None_)

The MongoDB object connects your Flask instance to a MongoDB server. To configure the application, you may pass the Flask app during the instantiation of the MongoDB object or using the `init_app` method.

<span class="class_attr">init_app</span>(_app_)

Configures the Flask instance with the MongoDB instance. This is the prefered method of configuration, especially when using the app factory method.

<span class="class_attr">register_collection</span>(_collection_cls_)

Registers a collection model to the MongoDB instance. 

** Parameters **

- `collection_cls`: Class of the model desired to be registered

<span class="class_attr">get_collection</span>(_collection_, _default=None_)

Retrieves registered collection model If the model is not registered, will return `None`. 

** Parameters **

- `collection`: Class of the model instance desired to be retrieved
- `default`: The default value to be returned if the collection is not registered


<span class="class_attr">disconnect</span>(_using='main'_)

Closes the connection of the desired database by alias.

** Parameters **

- `using`: Alias of the database to disconnect.

_property_ <span class="class_attr">collections</span>

Returns a dictionary of the registered collections.

_property_ <span class="class_attr">connections</span>

Returns a dictionary of the MongoDatabase instances.

## Collection Models

_class_ <span class="py_class">flask_mongodb.CollectionModel</span>(_\*\*field_values_)

The CollectionModel object is a representation of the collection in the database. 

<span class="class_attr">collection_name</span>

The name of the collection in the database. This attribute **MUST** be given or an error will be raised.

<span class="class_attr">db_alias</span>='main'

Default detabase alias the collection belongs to.
