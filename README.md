# ardilla

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ardilla) ![PyPI](https://img.shields.io/pypi/v/ardilla) ![GitHub](https://img.shields.io/github/license/chrisdewa/ardilla) 

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

For developers seeking a simple and straightforward way to incorporate a SQLite database into their applications, our library is an excellent option. It offers a user-friendly solution that is both fast and easy to use.

While this library may not be suitable for those who require more complex querying and intricate relationships, it excels in its simplicity and ease of implementation.

For developers who desire more advanced features, there are other libraries available, such as [tortoise-orm](https://github.com/tortoise/tortoise-orm), [sqlalchemy](https://github.com/sqlalchemy/sqlalchemy), [pony](https://github.com/ponyorm/pony) or [peewee](https://github.com/coleifer/peewee).


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

class User(Model):
    id: int = Field(primary=True, autoincrement=True) 
    name: str
    age: int

user_crud = engine.crud(User)

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

## To-dos

- [x] Add testing
- [x] Add a schema generator 
- [ ] Docstring everything using Google format
- [ ] Add proper documentation
  - propper as in a site with how to use
