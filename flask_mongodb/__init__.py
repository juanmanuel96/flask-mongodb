import sys
from flask_mongodb.about import PY_VERSION
from flask_mongodb.core.exceptions import PyVersionInvalid

# Python Version check
major, minor, micro = PY_VERSION.split('.')
if sys.version_info.major == int(major):
    if sys.version_info.minor < int(minor):
        raise PyVersionInvalid(f'Python version must greater than or equal to {PY_VERSION}')
else:
    raise PyVersionInvalid('Major version number must be 3')


from flask_mongodb.core.mongo import MongoDB
from flask_mongodb.core import exceptions
from flask_mongodb.core.mixins import ModelMixin
from flask_mongodb.models import CollectionModel
from flask_mongodb.serializers import Serializer, ModelSerializer
from flask_mongodb.globals import get_current_mongo, current_mongo

__all__ = (
    "MongoDB",
    "exceptions",
    "ModelMixin",
    "CollectionModel",
    "Serializer",
    "ModelSerializer",
    "get_current_mongo",
    "current_mongo"
)
