import sys
import traceback
import typing as t
from copy import deepcopy

from flask import Flask
from pymongo.errors import OperationFailure
from werkzeug.utils import import_string

from flask_mongodb import MongoDB
from flask_mongodb.core.exceptions import CouldNotRegisterCollection, FieldError
from flask_mongodb.core.wrappers import MongoCollection
from flask_mongodb.models.collection import CollectionModel
from flask_mongodb.models.fields import EmbeddedDocumentField, EnumField, ReferenceIdField, StructuredArrayField


def _enum_field_validators(field):
    if field.bson_type is not None:
        raise FieldError('The enum of the EnumField will establish the valid types')
    
    enum = {'enum': field.enum}
    if field.allow_null:
        field.bson_type = ['null']
    return enum['enum']


def _embedded_document_validators(field: EmbeddedDocumentField):
    sub_validators = {
        "bsonType": ['object'],
        "required": [],
        "properties": {}
    }
    
    if field.allow_null:
        sub_validators['bsonType'].append('null')
    
    for prop_name, prop_field in field.properties.items():
        if prop_field.required:
            sub_validators["required"].append(prop_name)
        
        sub_validators['properties'][prop_name] = {}
        
        # Defining field BSON types
        if prop_field.bson_type is not None:
            sub_validators["properties"][prop_name].update({"bsonType": deepcopy(prop_field.bson_type)})

            # If has BSON Type, check if null is allowed and add it
            if prop_field.allow_null:
                sub_validators['properties'][prop_name]["bsonType"].append('null')
        
        if max_length := getattr(prop_field, 'max_length', None):
            sub_validators["properties"][prop_name].update({'maxLength': max_length})

        if min_length := getattr(prop_field, 'min_length', None):
            sub_validators["properties"][prop_name].update({'minLength': min_length})
        
        if prop_field.description:
            sub_validators['properties'][prop_name].update({'description': prop_field.description})
        
        if isinstance(prop_field, EnumField):
            in_enum = _enum_field_validators((prop_field))
            sub_validators['properties'][prop_name].update(enum=in_enum)
        elif isinstance(prop_field, EmbeddedDocumentField):
            # Support for Embedded documents in embedded documents
            sub_sub_validators = _embedded_document_validators(prop_field)
            sub_validators['properties'][prop_name].update(sub_sub_validators)
        elif isinstance(prop_field, StructuredArrayField):
            struc_array_validators = _structured_array_validators(prop_field)
            sub_validators['properties'][prop_name].update(struc_array_validators)
        else:
            # It's another field, continue on
            pass

    if not sub_validators['required']:
        sub_validators.pop('required', None)  # If required field empty, remove it
    
    return sub_validators


def _structured_array_validators(field: StructuredArrayField):
        field_properties = {}
        if min_items := getattr(field, 'min_items', None):
            field_properties.update({'min_items': min_items})
        
        if max_items := getattr(field, 'max_items', None):
            field_properties.update({'max_items': max_items})
        
        items = {
            'bsonType': ['object'],
            'required': [],
            'properties': {}
        }
        
        for item_name, item_field in field.items.items():
            if item_field.required:
                items['required'].append(item_name)
            
            items['properties'][item_name] = {}
            
            if item_field.bson_type is not None:
                items['properties'][item_name].update({'bsonType': deepcopy(item_field.bson_type)})
                
                if item_field.allow_null:
                    items[item_name]['properties']['bsonType'].append('null')
            
            # Add max_length if it has it
            if max_length := getattr(item_field, 'max_length', None):
                items["properties"][item_name].update({'maxLength': max_length})

            # Add min_length if it has it
            if min_length := getattr(item_field, 'min_length', None):
                items["properties"][item_name].update({'minLength': min_length})
            
            if item_field.description:
                items['properties'][item_name].update(description=item_field.description)
            
            if isinstance(item_field, EmbeddedDocumentField):
                sub_validators = _embedded_document_validators(item_field)
                items['properties'][item_name].update(sub_validators)
            elif isinstance(item_field, EnumField):
                in_enum = _enum_field_validators(item_field)
                items['properties'][item_name].update({'enum': in_enum})
            elif isinstance(item_field, StructuredArrayField):
                struc_array_validators = _structured_array_validators(item_field)
                items['properties'][item_name].update(struc_array_validators)
            else:
                # It's another field, continue on
                pass
        
        if not items['required']:
            items.pop('required', None)
        
        field_properties.update(items=items)
        return field_properties


def define_schema_validator(model_instance):
    validators = {
            '$jsonSchema': {
                "bsonType": "object",
                "required": [],
                "properties": {}
            }
        }
    for name, field in model_instance.fields.items():
        if isinstance(field, ReferenceIdField):
            # If field is a ReferenceIdField, it will be ignored and it's counterpart [name]_id
            # will be used
            continue
        
        if hasattr(field, '_reference_manager'):
            # Do not consider reference managers
            continue
        
        if field.required:
            validators["$jsonSchema"]["required"].append(name)
        
        validators['$jsonSchema']['properties'][name] = {}
        
        # Defining field BSON types
        if field.bson_type is not None:
            # If bson_type attrib is not None, add it to the bson_types
            # Need to copy to avoid refrence modifications
            validators['$jsonSchema']["properties"][name].update({"bsonType": deepcopy(field.bson_type)})

            # Check if null is allowed and add it
            if field.allow_null:
                validators["$jsonSchema"]["properties"][name]["bsonType"].append('null')

        # Add min_length if it has it, applies only to StringField and PasswordField
        if min_length := getattr(field, 'min_length', None):
            validators["$jsonSchema"]["properties"][name].update({'minLength': min_length})
        
        # Add max_length if it has it
        if max_length := getattr(field, 'max_length', None):
            validators["$jsonSchema"]["properties"][name].update({'maxLength': max_length})
        
        if field.description:
            validators["$jsonSchema"]["properties"][name].update({'description': field.description})
        
        if isinstance(field, EnumField):
            enums = _enum_field_validators(field)
            validators['$jsonSchema']['properties'][name].update({'enum': enums})
        elif isinstance(field, EmbeddedDocumentField):
            embedded_validators = _embedded_document_validators(field)
            validators['$jsonSchema']['properties'][name].update(embedded_validators)
        elif isinstance(field, StructuredArrayField):
            structured_array_validators = _structured_array_validators(field)
            validators['$jsonSchema']['properties'][name].update(structured_array_validators)
        else:
            # It's another field, continue on
            pass
    
    if not validators['$jsonSchema'].get('required'):
        validators['$jsonSchema'].pop('required')  # Remove required field if empty list
    return validators if validators['$jsonSchema']['properties'] else {}


def create_collection(mongo: MongoDB, collection_cls: t.Type[CollectionModel]):
    _instance = collection_cls()
    schema_validators = define_schema_validator(_instance) if not _instance.schemaless else None
    database = mongo.connections[_instance.db_alias]
    try:
        # Will first try to create a collection
        MongoCollection(database, _instance.collection_name, create=True, 
                        validator=schema_validators,
                        validationLevel=_instance.validation_level if not _instance.schemaless else None)
    except OperationFailure as exc:
        if exc.code == 48:  # Collection exists
            raise CouldNotRegisterCollection('Collection already exists')
        traceback.print_exc()  # For information purposes if something else happens
        sys.exit(1)  # Stop execution


def start_database(mongo: MongoDB, app: Flask, database='all'):
    if not app.config['MODELS']:
        return None
    models_list = []
    created_collections = []
    
    # Prepare a list of modules with their models
    for mod in app.config['MODELS']:
        mod = mod + '.models'
        models = import_string(mod)
        models_list.append(models)
    
    # Itereate over the list and register the models
    for m in models_list:
        module_contents = dir(m)  # Get contents of the module
        for cont in module_contents:
            obj = getattr(m, cont)  # Get each object
            
            # Register the obj as a collection if it has the collection_name
            # and db_alias attributes which all models should have
            if hasattr(obj, 'collection_name') and hasattr(obj, 'db_alias'):
                if obj.collection_name is None:
                    # When the collection name is None, it is the base model class
                    continue
                if obj.collection_name in created_collections:
                    # This is to avoid moments when the models module imports another model
                    # Which migh have already been created
                    continue
                if database == 'all':
                    create_collection(mongo, obj)
                elif obj.db_alias == database:
                    create_collection(mongo, obj)
                created_collections.append(obj.collection_name)


def add_new_collection(mongo: MongoDB, app: Flask, database):
    if not app.config['MODELS']:
        return None
    models_list = []
    collections_added: t.List[str] = []
    
    # Prepare a list of modules with their models
    for mod in app.config['MODELS']:
        mod = mod + '.models'
        models = import_string(mod)
        models_list.append(models)
    
    # Itereate over the list and create the new collections
    for m in models_list:
        module_contents = dir(m)
        for cont in module_contents:
            obj = getattr(m, cont)
            if hasattr(obj, 'collection_name') and hasattr(obj, 'db_alias'):
                if obj.collection_name is None:
                    # When the collection name is None, it is the base model class
                    continue
                try:
                    create_collection(mongo, obj)
                    collections_added.append(obj.collection_name)
                except CouldNotRegisterCollection:
                    continue
    
    if collections_added:
        shift_model = mongo.collections[database]['shift_history']
        shift_model.set_model_data({
            'db_collection': 'Added collections: ' + ', '.join(collections_added)
        })
        shift_model.manager.insert_one(shift_model.data())
