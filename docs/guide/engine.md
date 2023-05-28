# Engines

## Basics

Ardilla offers two engines, the default `ardilla.Engine` which is a sync client powered by `sqlite3` and `ardilla.asyncio.Engine` which is an asynchronous engine powered by `aiosqlite`. 

They expose the same interface except the async engine uses `await` its methods.

To use the async engine you first need to install `aiosqlite` you can do it with any of the following methods:

```
pip install -U ardilla[async]
pip install -U ardilla, aiosqlite
```

## Use

The engine manages the connections and cursors for the crud methods.

The engine has the following parameters:

- path: A pathlike that points to the location of the database
- enable_foreing_keys: If true the engine will set `PRAGMA foreign_keys = ON;` in every connection.

```py
from ardilla import Engine

engine = Engine('path/to/database', enable_foreign_keys=True)

```

The engines work on single connections, and they can be used in two ways:

### classic open/close syntax
With this interface you can create the engine in any context and connect and close it when your app stars/end.
For the `AsyncEngine` you need `await` the methods.
```py
engine = Engine('db.sqlite')
engine.connect() # set up the connection
# work
engine.close()
```

### contextmanager
```py
with Engine('db.sqlite') as engine:
    # work
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

with Engine('db.sqlite') as engine:
    user_crud = engine.crud(User)
```


## Next

The [CRUD](crud.md) object and how to use it...
