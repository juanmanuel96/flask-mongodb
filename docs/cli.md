# The CLI Tool

Flask-MongoDB comes with a CLI tool to run database operations which are very hard to run during application runtime. Some examples are creating a database and its collections, or updating a collection when a field is altered or created. To run the CLI tool, open your terminal and execute the `flask-mongodb` command.

## Commands

This section will describe all of the command available with the CLI tool. Note that running the base command will print out the help guide, it is the same as using the --help flag.

The flask-mongodb is the main command for all other commands of the tool. Options available for this command: 

* --version: Prints out the package version
* --help: Prints out the help information

### create-model

This command will create a model file in the directory of your choosing. This command simply replaces the process of having to create manually each file or python package. Options for this command:

* --path: Path to where the file will be created, providing no path will create it in the location where the command is executed
* --package: Creates a package

### shift

The shift CLI group is used to generate database shift. In Flask-MongoDB database shifting is the concept of altering the database either by creating it or modifying an existing one. The CLI tool was born to satisfy this need of the package. This command cannot run alone on its own it has a set of subcommands that make the use of shifting possible.

#### start-db

This command creates databases to be used by your application. It should be ran once the databases have been defined in the configurations of the application. Models do not have to be created before hand to create the database, it would be ideal but not necessary. The `start-db` command has an option for specifying a model to be created.

Please note that with this package you can run your application without explicitly creating a database, but once you stop the application all data will be lost. This command must be ran whenerver a new model group has been created.

Options for this command:

* --all, -a: Creates all databases, avoid having to run the command database by database
* --database, -d: Specify the database alias to be started, default is `main`
* --path, -p: Model path with dot notation
* --help: Display help information

#### add-collections

This command will add new collections to your database after your model group has been created. Say you have a model group called `api.blog` with a model called `BlogPosts` where the author is a StringField. Then you wish to move the author data to another model called `Author`. Adding this new model would require a tense workaround. With the `add-collections` command, you will only have to define your model run the command. This command will add all new models to the database. 

Options for this command:

* --database, -d: Specify the database to add the collections, default is `main`
* --help: Display help information

#### history

This command will go through the `shift_hisotry` collection of the database and print the datetime and collection name that was shifted.

Options for this command:

* --database, -d: Specify the database to see the shift history, default is `main`
* --help: Display help information

#### examine

This command will compere a collection of the the databse current state, specifically the schema, with the collection model's schema. After the examination has been completed, the command will output detailing which colletions of the current database will require shifting. The examine will look for new fields, field alterations (e.g. changing a StringField to an EnumField), and

Options for this command:

* --database, -d: Specify the database to do the examination, by default it is set to main
* --collection, -c: Specify the collection name to examine
* --help: Display help information

#### run

The run command will execute the shifts necessary for the databases. Shifting does another examination before applying the shifts.

> **NOTE:** When the schema of the collection and the model have not changed at all, the shifting tool will treat this as another necessary shift. If a collection does not have data, the shift tool will also assume a shift is necessary. Everytime a shift is ran, a new entry in the database's shift history collection is inserted. Before running the `run` command, run the `examine` command first to see if a shift is necessary.

Options for this command:

* --database, -d: Specify the database on which to run the shift, default is main
* --collection, -c: Specify the collection to run the shift
