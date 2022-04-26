from flask import current_app
from werkzeug.local import LocalProxy

from flask_mongodb.core.mongo import MongoDB


__all__ = (
    'get_cuurent_mongo',
    'current_mongo'
)


current_mongo: "MongoDB" = LocalProxy(lambda: get_current_mongo())


def get_current_mongo() -> MongoDB:
    if not hasattr(current_app, 'mongo'):
        return None
    return current_app.mongo
