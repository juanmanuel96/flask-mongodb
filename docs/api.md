# API Reference

This part of the documentation covers all of the interfaces Flask-MongoDB has to offer. 

## The MongoDB object

_class_ <span class='py_class'>flask_mongodb.MongoDB</span>(_app=None_)

The MongoDB object connects your Flask instance to a MongoDB server. To configure the application, you may pass the Flask app during the instantiation of the MongoDB object or using the `init_app` method.

_meth_ <span class="class_attr">disconnect</span>(_using='main'_)

Closes the connection of the desired database by alias.

**Parameters**

- `using`: Alias of the database to disconnect.

_property_ <span class="class_attr">collections</span>

Returns a dictionary of the registered collections per database alias.

_property_ <span class="class_attr">connections</span>

Returns a dictionary of the MongoDatabase instances per database alias.

## Collection Models

_class_ <span class="py_class">flask_mongodb.models.collection.BaseCollection</span>()

The CollectionModel object is a representation of the collection in the database. 

_attr_ <span class="class_attr">collection_name</span>

The name of the collection in the database. This attribute **MUST** be given or an error will be raised.

_attr_ <span class="class_attr">db_alias</span>='main'

Default detabase alias the collection belongs to.

_attr_ <span class="class_attr">schemaless</span>=False

Defines if your collection has a schema or not.

_attr_ <span class="class_attr">validation_level</span>='strict'

MongoDB collection validation level.

_attr_ <span class="class_attr">manager_class</span>=<span class="class_attr">CollectionManager</span>

Manager class for the collection.

_property_ <span class="class_attr">manager</span>

Property for the manager instance. 

_proterty_ <span class="class_attr">fields</span>

Property for the model's fields.

_property_ <span class="class_attr">pk</span>

Property for the _id field of the model, the primary key.

_meth_ <span class="class_attr">connect</span>()

Create a connection between your model and the collection. 

> **NOTE:** This requires your application to be at the top of the context stack.

_meth_ <span class="class_attr">disconnect</span>()

Disconnect your model from the collection.

_meth_ <span class="class_attr">save</span>(_bypass_validation=False_)

Save model data in the data base.

**Parameters**

- `session`: Pymongo session.

- `bypass_validation`: Bypass document validation at the database level. While the option is available, it should be use as little as possible to avoid bad data in database.

- `comment`: A comment for the insert or update command.

_class_ <span class="py_class">flask_mongodb.CollectionModel</span>(_\*\*field_values_)

Inherits from BaseCollection. Base class for all your models to inherit from. Use keyword arguments to give initial values to your desired fields.

_meth_ <span class="class_attr">set_model_data</span>(_data_)

Sets the model fields values with the provided data. The `data` parameter must be a dictionary where the keys must be strings.

**Parameters**

* `data`: Data to give each field, keys must be string with the name of the fields

_property_ <span class="class_attr">collection</span>

Property for getting the `MongoCollection` instance. Will return `None` if the model hasn't been connected.

## Model fields

_class_ <span class='py_class'>flask_mongodb.models.fields.Field</span>(_required=True, allow_null=False, default=None, clean_data_func=None_)

Base class for all fields to inherit from.

**Parameters**

* `required`: Determine if the field is required, default `True`
* `allow_null`: Determine if null values are allowed, default `False`
* `default`: Default value of the field, default `None`
* `clean_data_func`: Function to be executed when fetching the field value, default `None`

_meth_ <span class="class_attr">set_data</span>(_value_)

This method sets the field's value. It must be overriden by child classes to properly assign the value with the correct type.

**Parameters**

* `value`: Value to set for the field

_meth_ <span class="class_attr">get_data</span>()

Returns the field's value. This method does not need to be overriden, but you can if you wish to do some opertation before the data is returned.

_meth_ <span class="class_attr">run_validation</span>(_value_)

Method for running the field's `validate_data` method if it has not been validated.

**Parameters**

* `value`: Value to be validated

_meth_ <span class="class_attr">validate_data</span>(_value_)

Method for validating the incomming data for the field. After it has been ran, it sets the `_validated` flag to True. When creating a custom field, this method's super must be executed after the validation logic.

**Parameters**

* `value`: Value to be validated

_meth_ <span class="class_attr">clean_data</span>()

Exevutes the `clean_data_func` if it has been provided, otherwise returns the field's value.

_meth_ <span class="class_attr">clear</span>()

Clears the field's value, sets it to None.

_property_ <span class="class_attr">data</span>

Property for the field's value. If the data is callable, the function is executed and the return value is returned. Otherwise, executes the `get_data` method.

_class_ <span class='py_class'>flask_mongodb.models.fields.ObjectIdField</span>(_required=True, allow_null=False, default=ObjectId_)

Field type that represents an ObjectId item in a MongoDB collection.

_class_ <span class='py_class'>flask_mongodb.models.fields.StringField</span>(_min_length=0, max_length=0, required=True, allow_null=False, default=''_)

Field type that represents an string item in a MongoDB collection.

_class_ <span class='py_class'>flask_mongodb.models.fields.PasswordField</span>

Inherits from `StringField`, but hashes the data.

_class_ <span class='py_class'>flask_mongodb.models.fields.IntegerField</span>(_required: bool = True, allow_null=False, default=0_)

Field type that represents an integer item in a MongoDB collection.

_class_ <span class='py_class'>flask_mongodb.models.fields.FloatField</span>(_required: bool = True, allow_null=False, default=0.0_)

Field type that represents a double item in a MongoDB collection.

## Managers

_class_ <span class='py_class'>flask_mongodb.models.manager.BaseManager</span>(_model=None_)

Manager class for all models. Takes in the current model as parameter. 

<span class="class_attr">find</span>(_\*\*filter_)

Returns a `DocumentSet` with all of the found documents set by the filter. To get all documents in the collection, do not provider a filter.

<span class="class_attr">all</span>()

This method is the same as running the `find` method without any filters.

<span class="class_attr">find_one</span>(_\*\*filter_)

Get the first document found by the filter. Returns in model representation of the document.as

<span class="class_attr">insert_one</span>(_insert_data=None, **options_)

Insert a single document into the database. With the `options` kwargs, you can pass pymongo and MongoDB optins to the pymongo counterpart method.

<span class="class_attr">update_one</span>(_query, update, update_type='$set', **options_)

Update the first document that meets the filter with the desired update. By default, the update type is set to `$set` but it can be modified to other MongoDB update types such as `$push`.

<span class="class_attr">delete_one</span>(_query, **options_)

Delete the first document that meets the query filter. 

<span class="class_attr">delete_many</span>(_query, **options_)

Delete all every document that meets the query filter. 

_class_ <span class='py_class'>flask_mongodb.models.manager.CollectionManager</span>(_model=None_)

Main manager class for all models. When creating a custom manager class, inherit from this class.

_class_ <span class='py_class'>flask_mongodb.models.manager.RefrenceManager</span>(_model=None, field_name=None_)

This manager handles the reverse references when a model has a RefrenceIdField. It inherits from the `BaseManager` class with only the `find`, `all`, and `find_one` methods enabled. 

## DocumentSet

_class_ <span class='py_class'>flask_mongodb.models.document_set.DocumentSet</span>(_model=None_)

A list-like object that represents the results of a query. Lazily loads each document in model representation.

**Parameters**

* `model`: Model class for the document set, default `None`

_meth_ <span class="class_attr">first</span>()

Get the first document in model representation of the query result.

_meth_ <span class="class_attr">last</span>()

Get the last document in model representation of the query result.

_meth_ <span class="class_attr">limit</span>(_number_)

Limit the number of documents from the query result.

**Parameters**

* `number`: Total documents to get from a larger set

_meth_ <span class="class_attr">sort</span>(_key_or_list, direction=None_)

Sort the document in the ordered desired. Use the same sorting convention you would use for a pymongo Cursor.

**Parameters**

* `key_or_list`: Key or list of keys to apply the sorting over
* `direction`: Direction to which make the sorting, default `None`. Use `pymongo.ASCENDING` or `pymongo.DESCENDING` for the `direction` parameter

_meth_ <span class="class_attr">count</span>()

Return the total number of documents from the query.

<span class="class_attr">run_cursor_method</span>(_meth_name, \*args, \*\*kwargs_)

Run a method from the cursor class in your document set. It cannot be a magic method (methods that begin with "_") nor any of the predefiend of the class, or the clone method.

**Parameters**

* `meth_name`: Name of the method of the cursor to run
* `*args`: Args to pass to the pymongo Cursor method
* `**kwargs`: Keyword arguments to pass to the pymongo Cursor method


## Serializers

_class_ <span class='py_class'>flask_mongodb.serializers.Serializer</span>(_data=None, formdata=None, obj=None, prefix="", meta=None, **kwargs_)

A data validation class.
