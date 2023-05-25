# Engines

## Basics

Ardilla offers two engines, the default `ardilla.Engine` which is a sync client powered by `sqlite3` and `ardilla.asyncio.Engine` which is an asynchronous engine powered by `aiosqlite`. 

To use the async engine you first need to install `aiosqlite` you can do it with any of the following methods:

```
pip install -U ardilla[async]
pip install -U ardilla, aiosqlite
```

Both engines have the same basic functionality. 

## Use

The engine manages the connections and cursors for the crud methods.

The engine has the following parameters:

- path: A pathlike that points to the location of the database
- enable_foreing_keys: If true the engine will set `PRAGMA foreign_keys = ON;` in every connection.
- single_connection: If true the engine will use a single connection and will have to be closed before exiting the program

```py
from ardilla import Engine

engine = Engine('path/to/database', enable_foreign_keys=True)

```

## The CRUD objects

The engines by themselves don't offer more than the connections but ardilla offers a CRUD class that has a one to one relation with Model subclasses. The Crud class requires the Model and engine as parameters so the engine offers a convenience method that works in three ways.

`engine.crud(Model)`

- returns the CRUD object for the specified Model.
- keeps a CRUD object/model cache, so that crud models are only instantiated once and returned every time the method is called
- calls the table creation to the database synchronously the first time the method is called.

## Using engine.crud

```py
from ardilla import Engine, Model

class User(Model):
    name: str

engine = Engine('my_db.sqlite')

user_crud = engine.crud(User)
```

## Single connection

The single connection mode is only available for now on the sync Engine, it will rise an error on the async Engine.
If a single connection is being used the user most close the database connection manually before the app closes

`engine.close()`

## Next

The [CRUD](crud.md) object and how to use it...
