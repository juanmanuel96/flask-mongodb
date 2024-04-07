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

## v0.1.0

### Features

- CollectionModel save and delete method
- Removed all DB schema generation from model and moved to CLI tool
- Fields keep track of current data and initial data
- New `run_save` and `run_delete` method for manager
- Updating a model representation data from `find` and `find_one` queries can now be saved 

### Fixes

- Fixed tests to meet new package standards
- Removed deprecated code
- Fixed issues with Enum field, reference field, and how data is accessed in an embedded document field
- Fixed broken behaviors of CLI tool
- When getting a model from DocumentSet, model representation od document sets model field values as inital

### Notes

This version reset will allow the package to be better managed and do the cleanup necessary to make the package behave better and be more efficient. 

<hr> 

## Versioning restart

The package originally reached version 1.8.2; however, it was decided to restart versioning (without deleting the history) since there were some errors left that needed to be managed before it was really Production ready.

