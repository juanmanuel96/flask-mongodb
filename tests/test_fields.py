import datetime

from flask_mongodb.models.fields import DatetimeField, DateField, PasswordField, EnumField


def test_datetime_field():
    field = DatetimeField(default=datetime.datetime.now)
    assert isinstance(field.data, datetime.datetime)


def test_date_field():
    field = DateField(default=datetime.datetime.now)
    assert isinstance(field.data, datetime.date)


def test_password_field():
    field = PasswordField()
    field.set_data('mypassword123')
    assert field.compare_password('mypassword123')


def test_enum_field_verbose():
    choices = (
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    )
    field = EnumField(choices=choices)
    field.set_data('a')

    assert field.verbose == 'A'

