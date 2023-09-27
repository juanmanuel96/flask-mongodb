import typing as t

from flask import current_app
from werkzeug.local import LocalProxy

from flask_mongodb.core.mongo import MongoDB


__all__ = (
    'get_current_mongo',
    'current_mongo'
)


current_mongo: "t.Optional[MongoDB]" = LocalProxy(lambda: get_current_mongo())  # type: ignore


def get_current_mongo() -> t.Optional[MongoDB]:
    if not hasattr(current_app, 'mongo'):
        return None
    return current_app.mongo  # type: ignore
