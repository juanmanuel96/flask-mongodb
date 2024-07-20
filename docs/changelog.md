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

## v0.2.0

### Features

- Sunsetting of the `setup.py` file for installing the project to adhere to PEP 518 and PEP 621
- Renamed to `legacy_setup.py` because for some reason my PIP prioritized `setup.py` and because I am lazy decided to rename it before deleting it.

### Fixes

- Fixes issue with install where installing the package would fail to install some dependencies due to how imports were done. I prefer to make this change before fixing the setup file to follow best practices.

### Notes

The reason behind the move to `pyproject.toml` file serves two purposes:

1. Moves in the direction of following more PEP guidelines
2. Resolve install issue
3. Begin the process to publish to PyPI

This is the correct path to finally have the proper PyPI package I've always dreamt about. 

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

