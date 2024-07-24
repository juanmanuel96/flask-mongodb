import pytest
from pymongo.errors import WriteError

from flask_mongodb.models.document_set import DocumentSet
from tests.fixtures import BaseAppSetup
from tests.model_for_tests.core.models import ModelForTest, ModelForTest2, ModelWithDefaultValues, \
    ModelWithEmbeddedDocument, ModelWithEnumField, VeryComplexModel


class TestModelInstance(BaseAppSetup):
    MODELS = ['tests.model_for_tests.core']

    def test_two_model_instances(self):
        m1 = ModelForTest2(title='This is the title of m1', body='This is the body text of m1')
        m2 = ModelForTest2(title='This is the title of m2')

        assert m2['body'] != m1['body']

    def test_embedded_document_default_values(self):
        m = ModelWithEmbeddedDocument(phone_number={'number': '7559991122'})
        assert not m['phone_number']['confirmed'].data

    def test_embedded_document_change(self):
        m = ModelWithEmbeddedDocument(phone_number={'number': '7559991122'})
        number = m['phone_number']['number']
        m['phone_number']['number'].set_data('88833399922')

        assert number.data != m['phone_number']['number']

    def test_field_value_change(self):
        text_replacement = 'This is an improved sample text'

        m1 = ModelForTest(sample_text='This is a sample text')
        m1['sample_text'] = text_replacement
        changes = m1.modified_fields()

        assert changes['sample_text'] == text_replacement, "Field data did not change"

    def test_embedded_document_field_change(self):
        m = ModelWithEmbeddedDocument(phone_number={'number': '7559991122'})
        m['phone_number']['number'].set_data('88833399922')
        changes = m.modified_fields()

        assert changes['phone_number.number'] == '88833399922', "Change not detected"


class TestModelOperations(BaseAppSetup):
    MODELS = ['tests.model_for_tests.core']

    def test_find_one_that_does_not_exist(self):
        m = ModelWithEmbeddedDocument().manager.find_one(**{'phone_number.number': "7664328912"})
        assert m is None

    def test_empty_insert_one(self):
        with pytest.raises(ValueError):
            ModelWithDefaultValues().manager.insert_one()

    def test_save_on_simple_model(self):
        ack = ModelWithDefaultValues().save()
        assert ack.acknowledged

    def test_save_on_model_with_embedded_document(self):
        model = ModelWithEmbeddedDocument(first_name='John', last_name='Doe', phone_number={'number': '7559991122'})
        ack = model.save()

        assert ack.acknowledged

    def test_manager_operation_return_data_type(self):
        model = ModelForTest()
        ds = model.manager.find()

        assert isinstance(ds, DocumentSet), \
            'find() should return a DocumentSet'

    def test_document_set_elements_are_models(self):
        model = ModelForTest()
        ds = model.manager.find()

        assert all([isinstance(item, ModelForTest) for item in ds]), \
            'All instances must be of the ModelForTest'

    @pytest.mark.skip(reason='Collection is no longer inimitable')
    def test_inimitable_object(self):
        model = ModelWithDefaultValues()
        instance: ModelForTest = model.manager.find().first()

        assert instance.collection is None, \
            "It seems that the collection was imitated"

    # @pytest.mark.skip(reason='Tested in first insert, enable when insert management is improved')
    def test_required_field(self):
        with pytest.raises(WriteError):
            ModelForTest2().manager.insert_one(body='This is the body')

    def test_update(self):
        model1 = ModelForTest()
        model1['sample_text'] = 'sample text changed'
        ack = model1.manager.run_save()

        assert ack.acknowledged

    def test_delete(self):
        model2 = ModelForTest2()
        model2.set_model_data({
            'title': 'title',
            'body': 'This is the body of the article'
        })
        model2.save()

        # Now fetch the new data
        same_model = model2.manager.find().first()
        ack = model2.manager.delete_one(query={'_id': same_model.pk})

        assert ack.acknowledged

    def test_enum_field_with_null_value(self):
        model = ModelWithEnumField(alcohol_enum_field=None)
        ack = model.save()

        assert ack.acknowledged

    def test_a_very_complex_model(self):
        model = VeryComplexModel(
            simple_field='Hello World!',
            embedded_field={
                'layer1_simple_field': 'Hello, world!',
                'layer1_embedded_field': {
                    'layer2_simple_field': 'Hello World!',
                    'layer2_enum_filed': 'b',
                    'layer2_array_field': ['Hello, world!']
                },
                'layer1_integer_field': 4
            },
            float_field=3.4
        )
        ack = model.save()

        assert ack.acknowledged

    def test_a_very_complex_model_with_null_values(self):
        model = VeryComplexModel(
            simple_field="Hello World",
            embedded_field={
                'layer1_simple_field': "World!",
                'layer1_embedded_field': {
                    'layer2_simple_field': "Hello",
                    'layer2_enum_filed': None,
                    'layer2_array_field': []
                },
                'layer1_integer_field': 3
            },
            float_field=55.6
        )
        ack = model.save()

        assert ack.acknowledged
