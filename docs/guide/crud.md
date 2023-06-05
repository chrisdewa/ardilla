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


In the next sections we go into detail on how to use the methods.
We'll work with these models
```py
class User(Model):
    id: int = Field(pk=True, auto=True)
    name: str
    age: int
```


### get_all

```py
users = crud.get_all()
```
Retrieves all the objects from the database. Works as a filterless `get_many`

### get many filters and orders objects at database level

```py
# get all users named chris
users = crud.get_many(name='chris')
```

```py
# get 20 users at most named chris and order them by age in descending order
users = crud.get_many(
    order_by={'age': 'DESC'},
    limit=20,
    name='chris'
)
```
The `order_by` parameter takes a dictionary where the keys must be the field names, and the values are either `"ASC"` or `"DESC"`. 
The `limit` parameter is an integer, following SQLite specification, a number less than 1 returns an empty list, a higher number returns
a list of at most that length.

### get_or_create

```py
result = crud.get_or_create(name='chris', age=35)
# result is a tuple of the object and a bool
# True if the object was newly created
obj, created = result
```
`get_or_create` returns a tuple that tells you if the object was newly created, if you don't care about if it was or not newly created, you can unpack the result like this `user,_ = crud.get_or_create(name='chris', age=35)`. 

### get_or_none
```py
user = crud.get_or_none(name='hdjkdhjaskhdsajkashasjk', age=999999)
# user is None
user = crud.get_or_none(name='chris', age=35)
# user is chris
```
Returns only a result if it already exists in the database, else, it returns the None value

### insert

```py
obj = crud.insert(name='chris', age=35)
```
We skip the id since we specified "auto" in the model schema and this translates to "autoincrement".
The object that was returned will have `__rowid__` and `id` fields filled up with data from the db.

### insert_or_ignore
```py
obj = crud.insert_or_ignore(id=2, name='moni', age=34)
# the obj here exists since it was newly created
obj2 = crud.insert_or_ignore(id=2, name='moni', age=34)
# the object is now None since it already existed
# the crud won't bring back the existing record
```
We specify the id at creation and we get the object back, but if we try to insert it again, the obj variablle will be `None`

### save_one

```py
u = get_or_none(name='moni')
# u is User(id=2, name='moni', age=34)
u.age += 1 # it's her birthday
crud.save_one(u)
```
To save an object to the database we can create a new instance of `User` or we can use one object from the database. It's best to use the save and delete methods with objects and fields that have either a `__pk__` field (primary key) or `__rowid__`. Objects returned from the db always have rowid, but if you create the object yourself then you need to specify it if the object doesn't have a primary key.

### save_many
```py
users = [User(name='user {n}', age=n) for n in range(10)]
crud.save_many(*users)
```
While the `save_many` method takes an arbitrary number of objects, that could be just one, it's better to use `save_one` for single records. The main difference is that save one uses `driver.execute` and save many uses `drive.executemany`

### delete_one
```
crud.delete_one(obj)
```
Deletes a single record from the database. If the model does not have a primary key, or the object hasn't set its primary key or `__rowid__` this method will delete the first record that it finds with the given fields

```py
class Item(Model):
    name: str 
    category: str

obj = Item(name='pen', category='office')

crud = engine.crud(Item)

crud.delete_one(obj)
```
In this snippet the `Item` model does not have a primary key set, so `delete_one` will delete any item that shares the same name and category.

### delete_many
The query for deletion is created based on the objects ids, or rowids. 
If none is set then an exception will be raised `BadQueryError`.
Works similarly to `delete_one` but the query is executed with inclusion like `"DELETE FROM item WHERE id IN (?, ?)"` where the placeholders are the ids of two objects.



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

## additional methods

### count

Count outputs an integer of the number of fields with non null values over a single column or the whole table.
You can further restring the number of rows with key words

```py
count = crud.count(age=35)
# number of items in the table where the "age" column has the value 35
```
