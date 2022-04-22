import json

class BaseFlaskMongodbException(Exception):
    default_message: str = None
    
    def __init__(self, message: str = None) -> None:
        """Base Exception class for all FlaskMongoDB exceptions

        Args:
            message (str, optional): Message to replace default exception message. Defaults to None.
        """
        self.message = message if message else self.default_message
        self.message.replace("'", "\"")
        super().__init__(self.message)
    
    @property
    def details(self):
        return {
            "message": self.message
        }


class PyVersionInvalid(BaseFlaskMongodbException):
    default_message = "Python version is not equal or greater than 3.10"


class MissingViewModelException(BaseFlaskMongodbException):
    default_message = "View Model must be specified"


class NotABlueprintView(BaseFlaskMongodbException):
    default_message = "This view does not belong to a blueprint"


class InvalidBaseClass(BaseFlaskMongodbException):
    default_message = "Invalid base class"
    

class URIMissing(BaseFlaskMongodbException):
    default_default_message = "MONGO_HOST and MONGO_PORT are required in configuration"


class DatabaseException(BaseFlaskMongodbException):
    default_message = "MONGO_DATABASE environment variable missing"


class CollectionException(BaseFlaskMongodbException):
    default_message = "Collection name attribute cannot be empty str or None"


class CollectionInvalid(BaseFlaskMongodbException):
    default_message = "Collection does not exist"


class ValidationError(BaseFlaskMongodbException):
    default_message = "The field value is not valid"


class ValidatorsException(BaseFlaskMongodbException):
    default_message = "This validator is not a callable function"
    
    @property
    def details(self):
        return json.loads(self.message)


class InvalidClass(BaseFlaskMongodbException):
    default_message = "{invalid_class} is not a valid class"

    def __init__(self, invalid_class, message: str =  None):
        self.default_message.format(invalid_class=invalid_class.__class__)
        super().__init__(message)


class InvalidChoice(BaseFlaskMongodbException):
    default_message = "Not a valid choice"