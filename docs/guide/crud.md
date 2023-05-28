# CRUD

## Basics

The CRUD objects are the functional bit of ardilla. They allow you to interact with the database to Create, Read, Update and Delete records.

## Methods

- `crud.insert` Inserts a record, rises errors if there's a conflict
- `crud.insert_or_ignore` Inserts a record or silently ignores if it already exists
- `crud.save_one` upserts an object
- `crud.save_many` upserts many objects
- `crud.get_all` equivalent to `SELECT * FROM tablename`
- `crud.get_many` returns all the objects that meet criteria
- `crud.get_or_create` returns an tuple of the object and a bool, True if the object was newly created
- `crud.get_or_none` Returns the first object meeting criteria if any
- `crud.delete_one` Deletes an object
- `crud.delete_many` Deletes many objects


Crud objects that return data (insert and get) return instances of their models, so the User crud will only return instances of User because it will only interact with this table.

If you require a more complex query you can use the engine directly, for example:


## Use with engine:

The easiest way to use crud objects is letting the engine manage the crud's connection. The recommended way of using cruds is:
```py
engine = Engine('db.sqlite')
with engine:
    crud = engine.crud(YourModel)
    # work
```

## Standalone use

Crud objects actually only need a model type and an sqlite3 (or aiosqlite) connection to work so you can use them in a standalone way, but then make sure to manage correctly the conenction and close it when your program ends.

```py
import sqlite3
from ardilla import Crud
crud = Crud(YourModel, sqlite3.connect('db.sqlite'))
```


