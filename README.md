# ardilla

[![Downloads](https://static.pepy.tech/badge/ardilla/month)](https://pepy.tech/project/ardilla) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ardilla) ![PyPI](https://img.shields.io/pypi/v/ardilla) ![GitHub](https://img.shields.io/github/license/chrisdewa/ardilla) 

<div style="text-align:center">
  <img 
    src="https://images-ext-2.discordapp.net/external/sxevZWKA4UIZWNyt352zkHLGWrUMw_PV_jGWLXGPh_I/https/repository-images.githubusercontent.com/638528340/a0238c4e-addf-4130-a0fe-9a458be6cdc9?width=200&height=150"
  >  
</div>

Ardilla (pronounced *ahr-dee-yah*) means "**SQ**uirre**L**" in spanish.

This library aims to be a simple way to add an SQLite database and 
basic C.R.U.D. methods to python applications.
It uses pydantic for data validation and supports a sync engine as well
as an async (aiosqlite) version.

## Who and what is this for:

This library is well suited for developers seeking to incorporate SQLite into their python applications to use simple C.R.U.D. methods.
It excels in its simplicity and ease of implementation while it may not be suitable for those who require more complex querying, intricate relationships or top performance.

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

crud = engine.crud(User)

def main():
    # get or none
    user = crud.get_or_none(id=1) # user with id of 1
    # get or create
    user2, was_created = crud.get_or_create(id=2, name='chris', age=35)
    # get many
    users = crud.get_many(name='chris') # all users named chris
    # save one
    user3 = User(id=3, name='moni', age=35)
    user.age += 1 # it's her birthday
    crud.save_one(user3)
    # save many
    crud.save_many(user, user2, user3)
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


## Examples:

- A simple [FastAPI](https://github.com/chrisdewa/ardilla/blob/master/examples/fastapi_app.py) application
- A reputation based discord [bot](https://github.com/chrisdewa/ardilla/blob/master/examples/rep_discord_bot.py)
- [basic usage](https://github.com/chrisdewa/ardilla/blob/master/examples/basic_usage.py)
- [basic usage with foreign keys](https://github.com/chrisdewa/ardilla/blob/master/examples/basic_usage_fk.py)

## To-dos

- [x] Add testing
- [x] Add a schema generator 
- [X] Add filtering
- [X] Add limiting
- [ ] Docstring everything using Google format
- [ ] Start a changelog when out of alpha
- [ ] Add proper documentation
  - propper as in a site with how to use