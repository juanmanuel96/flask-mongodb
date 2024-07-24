import pytest
from bson import ObjectId
from wtforms import fields, ValidationError, Form
from wtforms.validators import DataRequired, Length

from flask_mongodb.forms.collection import CollectionModelForm, CollectionModelFormMeta
from tests.fixtures import BaseAppSetup
from tests.model_for_tests.core.models import ModelForTest2, ModelWithEmbeddedDocument


class ModelForm(CollectionModelForm):
    title = fields.StringField(validators=[
        DataRequired(),
        Length(max=50)
    ])
    body = fields.StringField(validators=[
        DataRequired()
    ])

    class Meta(CollectionModelFormMeta):
        model = ModelForTest2


class EmbeddedDocumentForm(Form):
    number = fields.StringField(validators=[DataRequired()])
    confirmed = fields.BooleanField(default=False)
    confirmed_date = fields.DateTimeField(default=None)


class ModelFormEmbeddedDocument(CollectionModelForm):
    class Meta(CollectionModelFormMeta):
        model = ModelWithEmbeddedDocument

    phone_number = fields.FormField(EmbeddedDocumentForm)
    first_name = fields.StringField(validators=[DataRequired()])
    last_name = fields.StringField(validators=[DataRequired()])


class ModelFormWithoutMeta(CollectionModelForm):
    field1 = fields.StringField(validators=[DataRequired()])


class TestModelInstance(BaseAppSetup):
    MODELS = ['tests.model_for_tests.core']

    def test_form_instantiation(self):
        form = ModelForm()
        assert len(form.data.keys()) == 3

    def test_model_oid_switch(self):
        form = ModelForm(data={
            'oid': ObjectId(),
            'title': 'Test title',
            'body': 'Test body'
        })
        form.validate()
        d = form.data
        assert 'oid' not in d.keys()

    def test_model_form_block_save(self):
        form = ModelForm(data={
            'title': 'Test title',
            'body': 'Test body'
        })
        with pytest.raises(ValidationError):
            form.save()

    def test_model_form_save(self):
        form = ModelForm(data={
            'title': 'Test title',
            'body': 'Test body'
        })
        form.validate()
        form.save()
        assert isinstance(form.instance, ModelForTest2)

    def test_model_form_with_embedded_document(self):
        form = ModelFormEmbeddedDocument(data={
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': {
                'number': '1234567890'
            }
        })
        form.validate()
        res = form.save()
        assert res.acknowledged

    def test_requirement_of_model_in_meta(self):
        with pytest.raises(AttributeError):
            ModelFormWithoutMeta()
