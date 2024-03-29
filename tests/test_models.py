import pytest
from pymongo.errors import WriteError

from flask_mongodb.models.document_set import DocumentSet
from tests.fixtures import BaseAppSetup

from tests.model_for_tests.core.models import ModelForTest, ModelForTest2, ModelWithDefaultValues, \
    ModelWithEmbeddedDocument, ModelWithEnumField


class TestModelInstance(BaseAppSetup):
    MODELS = ['tests.model_for_tests.core']

    def test_two_model_instances(self):
        m1 = ModelForTest2(title='This is the title of m1', body='This is the body text of m1')
        m2 = ModelForTest2(title='This is the title of m2')

        assert m2['body'] != m1['body']

    def test_embedded_document_default_values(self):
        m = ModelWithEmbeddedDocument(phone_number={'number': '7559991122'})
        assert m['phone_number']['confirmed'] == False

    def test_embedded_document_change(self):
        m = ModelWithEmbeddedDocument(phone_number={'number': '7559991122'})
        number = m['phone_number']['number']
        m['phone_number']['number'] = '88833399922'

        assert number != m['phone_number']['number']

class TestModelOperations(BaseAppSetup):
    MODELS = ['tests.model_for_tests.core']

    def test_find_one_that_does_not_exist(self):
        m = ModelWithEmbeddedDocument().manager.find_one(**{'phone_number.number': "7664328912"})
        assert m == None

    def test_empty_insert_one(self):
        ack = ModelWithDefaultValues().manager.insert_one()
        assert ack.acknowledged

    def test_insert_one_with_some_fields(self):
        ack = ModelWithDefaultValues().manager.insert_one({'string_field': 'My name is...'})
        assert ack.acknowledged

    def test_manager_operation_return_data_type(self):
        model = ModelForTest()
        ds = model.manager.find()

        assert isinstance(ds, DocumentSet), \
            'find() should return a DocumentSet'

    def test_document_set_elemets_are_models(self):
        model = ModelForTest()
        ds = model.manager.find()

        assert all([isinstance(item, ModelForTest) for item in ds]), \
            'All instaces must be of the ModelForTest'

    def test_inimitable_object(self):
        model = ModelWithDefaultValues()
        instance: ModelForTest = model.manager.find().first()

        assert instance.collection is None, \
            "It seems that the collection was imitated"

    def test_required_field(self):
        model = ModelForTest2()
        model['body'] = 'This is the body'

        with pytest.raises(WriteError):
            model.manager.insert_one()

    def test_update(self):
        model1 = ModelForTest()
        model1['sample_text'] = 'sample text changed'
        ack = model1.manager.update_one(query={'_id': model1.pk}, update=model1.data(include_reference=False))

        assert ack.acknowledged

    def test_delete(self):
        model2 = ModelForTest2()
        model2.set_model_data({
            'title': 'title',
            'body': 'This is the body of the article'
        })
        model2.manager.insert_one()

        # Now fetch the new data
        same_model = model2.manager.find().first()
        ack = model2.manager.delete_one(query={'_id':same_model.pk})

        assert ack.acknowledged

    def test_enum_field_with_null_value(self):
        model = ModelWithEnumField(alcohol_enum_field=None)
        ack = model.manager.insert_one(model.data(include_reference=False))

        assert ack.acknowledged
