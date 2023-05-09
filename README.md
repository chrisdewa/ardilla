# ardilla

Ardilla (pronounced *ahr-dee-yah*) means "**SQ**uirre**L**" in spanish.

A very simple library to quickly add SQLite to your program.
It leverages pydantic for data validation and modeling.
It comes in sync (sqlite3) and async (aiosqlite) flavors.


## install
Install directly from github
__**Without asynchronous support**__
```bash
pip install git+https://github.com/chrisdewa/ardilla.git
```
__**With asynchronous support**__
```bash
pip install git+https://github.com/chrisdewa/ardilla.git#egg=ardilla[async]
```

## How to use:

**This section is greatly underdeveloped**

```py
from ardilla import Engine, Model, Crud

engine = Engine('db.sqlite3')
Crud.engine = engine

class User(Model):
    id: int
    name: str
    age: int

user_crud: Crud[User] = Crud(User)

def main():
    engine.setup() # creates tables 
    # get or none
    user = user_crud.get_or_none(id=1)
    # get or create
    user2, was_created = user_crud.get_or_create(id=2, name='chris', age=35)
    # save one
    user3 = User(id=3, name='moni', age=35)
    user_crud.save_one(user3)
    # save many
    user_crud.save_many(user, user2, user3)
    # get many
    users = user_crud.get_many(age=35)
```

## Supported CRUD methods:
 - `crud.get_or_none` Returns an object or None
 - `crud.insert_or_ignore` Inserts a record or silently ignores if it already exists
 - `crud.get_or_create` returns an tuple of the object and a bool, True if the object was newly created
 - `crud.get_all` equivalent to `SELECT * FROM tablename`
 - `crud.get_many` returns all the objects that meet criteria
 - `crud.save_one` upserts an object
 - `crud.save_many` upserts many objects
 - `crud.delete_one` deletes one object
 - `crud.delete_many` deletes many objects


## To-dos

- [ ] Docstring everything using Google format
- [ ] Add proper documentation
  - propper as in a site with how to use
- [x] Add a schema generator 
  - There should be a method to generate a table's schema off the pydantic model. 
- [ ] Add a method somewhere to fetch relationships. 
- [ ] Add examples
- [ ] Improve this readme