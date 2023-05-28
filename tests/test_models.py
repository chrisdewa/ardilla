import sqlite3
from pathlib import Path
from datetime import datetime

from ardilla import Model, Field
from ardilla.errors import ModelIntegrityError

from pydantic import Json


def test_default_tablename():
    class Foo(Model):
        id: int
    
    assert Foo.__tablename__ == "foo"

def test_field_pk():
    class Foo(Model):
        id: str = Field(primary=True)
    
    assert Foo.__pk__ == 'id'

def test_int_pk_auto():
    class Foo(Model):
        id: int = Field(pk=True, auto=True)
    
    schema = Foo.__schema__
    assert 'id INTEGER PRIMARY KEY AUTOINCREMENT' in schema



binary_data = b'some weird data'

class Complex(Model):
    id: int = Field(pk=True, auto=True)
    created: datetime = Field(auto=True)
    name: str = 'me'
    lastname: str | None = None
    foo: str
    data: bytes = binary_data


def test_default_schema():
    complex_schema = f'''
    \rCREATE TABLE IF NOT EXISTS complex(
    \r    id INTEGER PRIMARY KEY AUTOINCREMENT,
    \r    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    \r    name TEXT DEFAULT 'me',
    \r    lastname TEXT,
    \r    foo TEXT NOT NULL,
    \r    data BLOB DEFAULT (X'{binary_data.hex()}')
    \r);
    '''
    assert Complex.__schema__.strip() == complex_schema.strip()


def test_complex_schema_works():
    try:
        db = Path(__file__).parent / 'db.sqlite3'
        db.unlink(missing_ok=True)
        con = sqlite3.connect(db)
        con.execute(Complex.__schema__)
        con.commit()
    finally:
        con.close()
        db.unlink(missing_ok=True)


class User(Model):
    id: int = Field(primary=True)
    name: str


tablename = "user"
schema = """
CREATE TABLE IF NOT EXISTS user(
\r    id INTEGER PRIMARY KEY,
\r    name TEXT NOT NULL
);
"""

def test_default_schema():
    assert User.__schema__.strip() == schema.strip()


def test_pk():
    assert User.__pk__ == "id"

def test_double_pks():
    try:
        class Book(Model):
            id: int = Field(pk=True)
            name: str = Field(pk=True)
    except Exception as e:
        assert isinstance(e, ModelIntegrityError)