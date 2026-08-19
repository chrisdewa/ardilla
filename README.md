

# ardilla

[![Downloads](https://static.pepy.tech/badge/ardilla/month)](https://pepy.tech/project/ardilla) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ardilla) ![PyPI](https://img.shields.io/pypi/v/ardilla) ![GitHub](https://img.shields.io/github/license/chrisdewa/ardilla) [![Documentation Status](https://readthedocs.org/projects/ardilla/badge/?version=latest)](https://ardilla.readthedocs.io/en/latest/?badge=latest)


<div style="text-align:center">
  <img 
    src="https://images-ext-2.discordapp.net/external/x805WO_foe1CtyWMNyUDl26wNryhN5MmJzBhs6JGKOU/https/repository-images.githubusercontent.com/638528340/5dec5f3d-1af7-420a-89bc-465fae9f3875?width=200&height=150"
  >  
</div>

Ardilla (pronounced *ahr-dee-yah*) means "**SQ**uirre**L**" in spanish.

This library aims to be a simple way to add an SQLite database and
basic C.R.U.D. methods to Python applications.
It uses **pydantic v2** for data validation and supports both a sync engine and
an async (aiosqlite) version.

## Who and what is this for

This library is well suited for developers seeking to incorporate SQLite into their Python applications using simple C.R.U.D. methods.
It excels in its simplicity and ease of implementation, but may not be suitable for those who require complex querying, intricate relationships, or top performance.

For more advanced features, consider [tortoise-orm](https://github.com/tortoise/tortoise-orm), [sqlalchemy](https://github.com/sqlalchemy/sqlalchemy), [pony](https://github.com/ponyorm/pony), or [peewee](https://github.com/coleifer/peewee).


## Links

Source code: [github.com/chrisdewa/ardilla](https://github.com/chrisdewa/ardilla)

Documentation: [ardilla.rtfd.io](http://ardilla.rtfd.io/)

## Install

Install the latest release from PyPI:
```bash
pip install -U ardilla
pip install -U ardilla[async]  # includes aiosqlite
pip install -U ardilla[dev]    # includes formatting and testing dependencies
pip install -U ardilla[examples]  # includes fastapi and uvicorn for the examples
```

Or install the latest changes directly from GitHub:
```bash
pip install git+https://github.com/chrisdewa/ardilla.git
pip install git+https://github.com/chrisdewa/ardilla.git#egg=ardilla[async]
pip install git+https://github.com/chrisdewa/ardilla.git#egg=ardilla[dev]
```


## How to use

```python
from ardilla import Engine, Model, Field

class User(Model):
    id: int = Field(pk=True, auto=True)
    name: str
    age: int

with Engine('db.sqlite') as engine:
    crud = engine.crud(User)
    user = crud.get_or_none(id=1)
    user2, was_created = crud.get_or_create(id=2, name='chris', age=35)
    users = crud.get_many(name='chris')
    user3 = User(id=3, name='moni', age=35)
    user2.age += 1
    crud.save_one(user3)
    crud.save_many(user2, user3)
```

## Supported CRUD methods

- `crud.insert` — inserts a record, raises an error on conflict
- `crud.insert_or_ignore` — inserts a record, silently ignores if it already exists
- `crud.save_one` — upserts a single object
- `crud.save_many` — upserts multiple objects
- `crud.get_all` — equivalent to `SELECT * FROM tablename`
- `crud.get_many` — returns all objects matching the given criteria
- `crud.get_or_create` — returns a tuple of `(object, created: bool)`
- `crud.get_or_none` — returns the first matching object, or `None`
- `crud.delete_one` — deletes a single object
- `crud.delete_many` — deletes multiple objects


## Examples

- A simple [FastAPI](https://github.com/chrisdewa/ardilla/blob/master/examples/fastapi_app.py) application
- A reputation-based Discord [bot](https://github.com/chrisdewa/ardilla/blob/master/examples/rep_discord_bot.py)
- [Basic usage](https://github.com/chrisdewa/ardilla/blob/master/examples/basic_usage.py)
- [Basic usage with foreign keys](https://github.com/chrisdewa/ardilla/blob/master/examples/basic_usage_fk.py)
