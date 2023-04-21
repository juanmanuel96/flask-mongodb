# Serializers

Serializers are classes used to validate incoming data. It is implemented with WTForms. There are two types of serializers:

* Serializer
* ModelSerializer

## Serializer class

This basic serializer class can work outside of the application context. In escence it accepts some incomming data and applies the values to each of the defined fields. The, you run the `is_valid` method to validate each of the fields. If any errors happen, you can see each of the errors with the `errors` attribute, which is a list of the errors. 

The incomming data can be a dictionary where the keys are the fields and the values the values of the fields. This type of data MUST be passed to the serializer on initialization with the `data` parameter or as the first parameter value. If you wish to use the `POST` attribute from the request proxy from Flask, you can use it as well. However, you need to specify the keyword argument `formdata`. Know that you cannot use `data` and `formdata` at the same time, a `ValueError` will be raised.

### CSRF Support 

By default, the Serializer class does not implement CSRF. For validating data, this will most probably not be required. However, as menthoned above, the Serializer class inherits from the WTForms and CSRF can be implemented. This needs to be done manually.

### Serializer meta class

The Serializer has a meta class, set by the `Meta` class attribute which exists to disable CSRF. The easiest way to enable CSRF is by inheriting the `SerializerMeta` class and create your own meta class.

### Fields

To add field to your Serializer, simply import the desired field from the wtfroms package and implement them the same way you would with a wtfoms Form class.

#### JSONField

The JSONField class is a custom flask-mongodb field for implementing Serializers that require a JSON-like structure. It is very similar to the FormField class, excpet that it is somewhat modified for flask-mongodb Serializer class.

#### Validators

Once again you can use wtforms validators on your fields. There is a custom validator called `AllowNull` for when a field requires data but a null value is allowed. 

#### Validation

When creating a custom validator in you Serializer class, use the same naming convention you would use in WTForms. If a validation error must be raised, use the `ValidationError` from WTForms.

## ModelSerializer class

The ModelSerializer class expands the Serializer class to accept a collection model with the class attribute `serializer_model`. This class has two properties for accessing the model or the manager for easier DB operations.
