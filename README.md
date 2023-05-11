# ardilla

<div style="text-align:center">
  <img 
    src="https://images-ext-2.discordapp.net/external/sxevZWKA4UIZWNyt352zkHLGWrUMw_PV_jGWLXGPh_I/https/repository-images.githubusercontent.com/638528340/a0238c4e-addf-4130-a0fe-9a458be6cdc9?width=200&height=150"
  >  
</div>

Ardilla (pronounced *ahr-dee-yah*) means "**SQ**uirre**L**" in spanish.

A very simple library to quickly add SQLite to your program.
It leverages pydantic for data validation and modeling.
It comes in sync (sqlite3) and async (aiosqlite) flavors.

## Who and what is this for:

The target audience for this library are developers who want to incorporate a SQLite database to their applications in a fast and easy way. 

What this library excels in simplicity it lacks in flexibility so, if you're expecting to use complex queries and intricate relationships, you should should consider other libraries like [tortoise-orm](https://github.com/tortoise/tortoise-orm), [sqlalchemy](https://github.com/sqlalchemy/sqlalchemy), [pony](https://github.com/ponyorm/pony) or [peewee](https://github.com/coleifer/peewee).


## install
Install lastest release from PyPi
```bash
pip install -U ardilla
pip install -U ardilla[async]
pip install -U ardilla[dev]
```
- async instaslls aiosqlite
- dev installs formatting and testing dependencies

Or install the lastest changes directly from github
```bash
pip install git+https://github.com/chrisdewa/ardilla.git
pip install git+https://github.com/chrisdewa/ardilla.git#egg=ardilla[async]
pip install git+https://github.com/chrisdewa/ardilla.git#egg=ardilla[dev]
```


## How to use:
```py
from ardilla import Engine, Model, Crud
from pydantic import Field

engine = Engine('db.sqlite3')
Crud.engine = engine

class User(Model):
    id: int = Field(primary=True, autoincrement=True) 
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
 - `crud.insert` Inserts a record, rises errors if there's a conflict
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
- [ ] Add testing
- [ ] Add proper documentation
  - propper as in a site with how to use
- [x] Add a schema generator 
  - There should be a method to generate a table's schema off the pydantic model. 
- [ ] Add a method somewhere to fetch relationships. 
- [ ] Improve this read