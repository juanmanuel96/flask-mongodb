from wtforms.validators import (AnyOf, DataRequired, Email, EqualTo, Length,
                                NoneOf, NumberRange, Optional, IPAddress)


class ValidationError(ValueError):
    def __init__(self, message="", *args: object) -> None:
        super().__init__(message, *args)


class StopValidation(Exception):
    def __init__(self, message=None, *args: object) -> None:
        if message:
            # If a message is added, it is removed because we do not
            # want to count it as an error
            message = None
        super().__init__(message, *args)


class AllowNull(Optional):
    def __call__(self, form, field):
        if (field.data is None):
            field.errors[:] = []
            raise StopValidation()


ip_address = IPAddress
required = DataRequired
same_as = EqualTo
length = Length
any_of = AnyOf
none_of = NoneOf
optional = Optional
number_range = NumberRange
email_validator = Email
allow_null = AllowNull
