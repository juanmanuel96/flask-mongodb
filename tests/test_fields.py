from flask_mongodb.models.fields import EnumField


def test_enum_field():
    EnumField(allow_null=True, default=None, choices=(('choice_1', 'choice 1'),
                                                      ('choice_2', 'choice 2')))
    assert True
