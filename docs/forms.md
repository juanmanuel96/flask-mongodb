# CollectionModelForm

To validate data for a collection model, Flask-MongoDB comes prepackaged with a class called `CollectionModelForm`. This class is an extension of the Form class of WTForms. 

## How to use

In this section, we shall create a CollectionModelForm linked with your collection model and how to use it.

### Creating a form

The following example demonstrates how to create a form.

```python
from flask_mongodb.forms.collection import CollectionModelForm
from flask_mongodb.forms.meta import CollectionModelFormMeta
from flask_mongodb.models import CollectionModel, fields
from wtforms import StringField, validators

class MyModel(CollectionModel):
    collection_name = 'my_collection'
    field1 = fields.StringField()

class FormExample(CollectionModelForm):
    class Meta(CollectionModelFormMeta):
        model = MyModel
    field1 = StringField(validators=[validators.DataRequired()])  # Make sure field requirements match that of the model
```

The first thing you should notice is the `Meta` class in the form. While typically this is hidden when normally creating a WTForms Form object, it should be defined for the `CollectionModelForm` class since you need to define which model the form is related to. This `Meta` class must always inherit from `CollectionModelFormMeta` and specify the model with the `model` attribute.

You should then define the form fields. To avoid issues with the model field's requirements, make sure to add all needed validators to the field that match the field requirements. This is also very important for the DataRequired since by default fields of WTForms are not required and in FlaskMongoDB they are.

### Validating data

Form data validation is done as you would for any other WTForms form validation. The following is an example of such operation.

```python
data = {
    'field1': 'sample text'
}
form = FormExample(data=data)
form.validate()
```

The recommended use for the form is to pass data to the form using the `data` parameter. However, the `formdata` parameter will work as well.

### Saving form data

After the form has been instantiated and validated, you can use the form's `save` method to save the data in the database. You can save as follows.

```python
form.save()
```

This method will raise a WTForms `ValidationError` if the save operation is attempted and the `validate` method has not been called.

## Some more notes

### The instance attribute

Every time you save the form, the form's `instance` attribute is updated. This attribute is the instantiated model with the data assigned as its initial values. It can then be accessed without the need to make a `find_one` operation.

### `_id` field

All CollectionModel classes have an automatic field labeled `_id`. It represents the \_id field of a document in a MongoDB collection. WTForms does not like fields that begin with an underscore (\_). For this reason, all `CollectionModelForm` objects come with a field labeled `oid`. It stands for ObjectId, and it's a renaming of the `_id` field. To get it as `_id`, the `data` method replaces `oid` with `_id` when ever called. 

### EmbeddedDocumentField in the form

If your collection has an EmbeddedDocumentField in the model, you can recreate this with the `FormField` field class of WTForms. The `FormField` class takes a Form object as one of its arguments. Simply, create a new Form class (you can use WTForms `Form` class or `CollectionModelForm` class) with the fields and field requirements matching that of the EmbeddedDocumentField and pass it to the `FormField` object. Here is an example.

```python
from flask_mongodb.forms.collection import CollectionModelForm
from flask_mongodb.forms.meta import CollectionModelFormMeta
from flask_mongodb.models import CollectionModel, fields
from wtforms import Form, FormField, StringField


class MyModel(CollectionModel):
    collection_name = 'my_model'
    top_level_field = fields.StringField(required=False)
    embedded_document = fields.EmbeddedDocumentField(required=False, properties={
        'sample_field': fields.StringField(required=False)
    })


class EmbeddedDocumentForm(Form):
    sample_field = StringField()

    
class MySampleForm(CollectionModelForm):
    class Meta(CollectionModelFormMeta):
        model = MyModel
    
    top_level_field = StringField()
    embedded_document = FormField(EmbeddedDocumentForm)
```

Use the form as you would use any other CollectionModelForm.

## Integration with Flask-WTF

As of this moment, the CollectionModelForm does not integrate well with Flask-WTF's FlaskForm. The Meta class in `FlaskForm` is defined the same way you would define the meta class here. While this issue is resolved, a workaround is to copy the CSRF stuff from the FlaskForm to the Meta class of `CollectionModelForm` as well as the FlaskForm method `validate_on_submit`.
