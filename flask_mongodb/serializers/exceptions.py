from flask_mongodb.core.exceptions import BaseFlaskMongodbException


class InvalidIncomingData(ValueError):
    def __init__(self, message="Incoming data should be dictonary", *args: object) -> None:
        super().__init__(message, *args)


class MissingSerializerModel(BaseFlaskMongodbException):
    default_message = "Serializer Model must be specified"
