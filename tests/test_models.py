import pytest
from flask import Flask
from pymongo.errors import WriteError

from flask_mongodb import MongoDB, exceptions
from flask_mongodb.core.wrappers import MongoConnect
from flask_mongodb.models import CollectionModel
from flask_mongodb.models.document_set import DocumentSet
from tests.fixtures import BaseAppSetup

from tests.model_for_tests.core.models import ModelForTest, ModelForTest2
from tests.utils import MAIN, remove_collections


class TestCollectionModels(BaseAppSetup):
    MODELS = ['tests.model_for_tests.core']

    def test_record_creation(self, mongo: MongoDB):
        model = mongo.get_collection(ModelForTest)
        model['sample_text'] = 'This is just a sample text'
        ack = model.manager.insert_one(model.data(include_reference=False))
        
        assert ack, 'Insert was not successfull'

    def test_getting_data_from_db(self, mongo: MongoDB):
        model = ModelForTest()
        ds = model.manager.find()
        
        assert isinstance(ds, DocumentSet), \
            'find() should return a DocumentSet'

    def test_document_set_elemets_are_models(self, mongo: MongoDB):
        model = ModelForTest()
        ds = model.manager.find()
        
        assert all([isinstance(item, ModelForTest) for item in ds]), \
            'All instaces must be of the ModelForTest'

    def test_inimitable_object(self, mongo: MongoDB):
        model = ModelForTest()
        instance: ModelForTest = model.manager.find().first()
        
        assert instance.collection is None, \
            "It seems that the collection was imitated"

    def test_required_field(self, mongo: MongoDB):
        model = ModelForTest2()
        model['body'] = 'This is the body'
        
        with pytest.raises(WriteError):
            model.manager.insert_one(model.data(include_reference=False))

    # def test_badly_configured_model(self, mongo: MongoDB):
    #     class BadlyConfiguredModel(CollectionModel):
    #         db_alias = None
    #         collection_name: str = 'bad'
        
    #     with pytest.raises(exceptions.CollectionException):
    #         mongo.register_collection(BadlyConfiguredModel)

    # def test_unnamed_collection(self, mongo: MongoDB):
    #     class UnnamedCollection(CollectionModel):
    #         collection_name: str = None
        
    #     with pytest.raises(exceptions.CollectionException):
    #         mongo.register_collection(UnnamedCollection)
    
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
        model2.manager.insert_one(model2.data(include_reference=False))
        
        # Now fetch the new data
        same_model = model2.manager.find().first()
        ack = model2.manager.delete_one(query={'_id':same_model.pk})
        
        assert ack.acknowledged
    
    def test_two_model_instances(self):
        m1 = ModelForTest2(title='This is the title of m1', body='This is the body text of m1')
        m2 = ModelForTest2(title='This is the title of m2')
        
        assert m2['body'] != m1['body']
