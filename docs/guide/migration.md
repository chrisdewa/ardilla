# Migration 

While Ardilla doesn't provide a migration manager like alembic (sqlalchemy) or aerich (tortoise) it does provide a simple migration script generator

## Use:

Import the function and generate the script by passing the old and new models and the original tablename (what the tablename is in the database)

```python
import sqlite3
from ardilla import Model, Field, Engine
from ardilla.migration import generate_migration_script

class User(Model):
    id: int = Field(pk=True, auto=True)
    name: str
    foo: int

class NewUser(Model):
    __tablename__ = 'users' # change the tablename
    id: int = Field(pk=True, auto=True)
    name: str = 'unset' # add a default
    age: int = 0 # add a new column "age" with default of "0"
    # drop the foo column


migration_script = generate_migration_script(
    User, NewUser,
    original_tablename='user',
    new_tablename='users',
)

con = sqlite3.connect('database.sqlite')
con.executescript(migration_script)
con.commit()
con.close()
```

## Limitations:

The migration script generator can't handle adding foreign key fields, unique fields or adding a not null field without a default.

