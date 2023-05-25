# Models

## Basics

`ardilla.Model` inherits directly from `pydantic.BaseModel` and adds most of the added functionality through the `Model.__init_subclass__` method. 

On subclassing, the `Model` will grab the fields and private attributes and populate three private attributes:

- `__schema__`: The SQLite table schema for the model.
- `__pk__`: The private key column name if any.
- `__tablename__`: The name of the table

The user can set these fields by themselves to provide additional of special configurations Ardilla might not do on its own.

To create a basic table you only need a single field and its type annotations.

```py
from ardilla import Model

class User(Model):
    name: str
```

This will create the following table schema:

```sql
CREATE TABLE IF NOT EXISTS user(
    name TEXT NOT NULL
);
```

You can also set default values right away by specifying a value for the field


```py
from ardilla import Model

class User(Model):
    name: str = 'John Doe'
```

This will create the following table schema:

```sql
CREATE TABLE IF NOT EXISTS user(
    name TEXT DEFAULT 'John Doe'
);
```

## Customize table name

By default the generated tablename is just the lowercase name of the model.
you can edit the tablename by setting yourself this private attribute

```py
from ardilla import Model

class User(Model):
    __tablename__ = 'users'
    name: str = 'John Doe'
```
Will generate the schema:
```sql
CREATE TABLE IF NOT EXISTS users(
    name TEXT DEFAULT 'John Doe'
);
```

## Next

To build more complex table models you need to learn about [Fields](fields.md)...