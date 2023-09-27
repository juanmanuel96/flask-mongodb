# Changelog

The structure for the changelog will be the following:

```
## Version Number
### Features
    - New stuff
### Fixes
    - Fixed stuff
### Notes
    - Notes if the release has any
```

<hr>

## v1.8.2

### Features

* No new features.

### Fixes

* `EnumField` issue with `allow_null` and default value being `None`
* Documentation grammatical errors fixed
* Other styles improvements

### Notes

1. This changelog does not have a log for v1.8.1. This was a mistake when deploying the said version.

## v1.8.0

### Features

* The `insert_one` command now can run without having to add insertion data, the model's data is now used
* Added new shift command to add new collections to database

### Fixes

* Fixed issue with model instantiation where all instances shared the last field value assigned of each value.
* Fixed issue with serializers using WTForms fields where during the processing of data
* Fixed issue with EmbeddedDocumentField where if only one field was to be updated, it required all other fields to be present in the update
* Fixed issue with `find_one` command where it raised an IndexError is no results where found in the database
* When referencing a model in another model, the referenced model can be given as data and not just the model's pk
* Serializers will now require WTForms' `ValidationError` when raising a validation error

### Notes
- The `data` method has been deprecated and will be removed as of version 2
- Old methods like `register_collection` and `get_collection` are no longer useful, especially the former

## v1.7.1

### Features

* None

### Fixes

* Fixed `history` command of the CLI tool`.

## v1.7.0

### Features

* CLI Tool
  * create-model command
  * shift command
    * examine
    * history
    * run
    * start-db
* Serializer improvements
* Ability to import models diretly in your code without having to use the `get_collection` method and apply field values during initialization of model.
* Refre

### Fixes

* DocumentSet methods are now usable
* Serializers can do database operations

