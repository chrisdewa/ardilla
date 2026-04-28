# Fields

## Basics

Every model public attributes are automatically set as table columns.
You can customize and extend the fields using `ardilla.Field` and `ardilla.ForeignField`.

`ardilla.Field` is a wrapper around `pydantic.Field` that accepts additional ardilla-specific keywords (`pk`, `primary`, `primary_key`, `auto`, `unique`) and stores them in `json_schema_extra` so ardilla can read them during schema generation. All other keyword arguments are forwarded directly to `pydantic.Field`.

`ardilla.ForeignField` is a `pydantic.fields.FieldInfo` subclass that serves as a helper for foreign key constraints.

## Usage

To extend the functionality of an `ardilla.Model` import `ardilla.Field` and use it on your fields.
The special keywords to use with fields are:

- `default`: Sets the default value for the field.
- `pk` / `primary` / `primary_key`: Mark this field as the primary key (all three are equivalent aliases).
- `auto`: Exclude this field from INSERT statements so the database populates it automatically. Valid for:
  - `int` fields that are primary keys — adds `AUTOINCREMENT`.
  - `datetime`, `date`, and `time` fields — adds `DEFAULT CURRENT_TIMESTAMP/CURRENT_DATE/CURRENT_TIME`.
  - When `auto=True` the field's default is set to `None` automatically (do not combine with `default_factory`).
- `unique`: Add a `UNIQUE` constraint on this column; raises a conflict error if violated.

```py
from datetime import datetime
from ardilla import Model, Field

class User(Model):
    id: int = Field(pk=True, auto=True)
    name: str = Field(unique=True)
    age: int # not null field
    money: float = 0.0
    created_date: datetime = Field(auto=True)
```

This Model will generate the following table schema:
```sql
CREATE TABLE IF NOT EXISTS user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    money REAL DEFAULT 0.0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
Or, as a table:

| id | name | age | money | created_date |
|----|------|-----|-------|--------------|
| 1  |chris | 35  | -10   | 1988-05-27-7 |


## Foreign key support

To set fields with foreign keys, use the foreign field helper `ardilla.ForeignField`

```py
from ardilla import Model, Field, ForeignField

class Author(Model):
    id: int = Field(pk=True, auto=True)
    name: str

class Book(Model):
    name: str
    author_id: int = ForeignField(
        references=Author, # the model with the referenced key
        on_delete=ForeignField.CASCADE,
        on_update=ForeignField.SET_NULL
    )
```
This will generate the following schema for the Book model:
```sql
CREATE TABLE IF NOT EXISTS book(
    name TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES author(id) ON UPDATE SET NULL ON DELETE CASCADE
);
```


## Next

To put your models to use you'll need a an [engine](engine.md)...