# CRUD

## Basics

The CRUD objects are the functional bit of ardilla. They allow you to interact with the database to Create, Read, Update and Delete records.

## Use

After getting your crud object from the engine `crud = engine.crud(Model)` you can access its methods:

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

```py
with engine as connection:
    with connection.execute(your_query, your_values) as cursor:
        ...
```
