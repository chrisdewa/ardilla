import sqlite3
from pathlib import Path
from datetime import datetime, date, time

import pytest

from ardilla import Model, Field
from ardilla.errors import ModelIntegrityError
from ardilla.fields import ForeignField


# ---------------------------------------------------------------------------
# Tablename
# ---------------------------------------------------------------------------

def test_default_tablename():
    class Foo(Model):
        id: int

    assert Foo.__tablename__ == "foo"


def test_custom_tablename():
    class Foo(Model):
        __tablename__ = "bars"
        id: int

    assert Foo.__tablename__ == "bars"


# ---------------------------------------------------------------------------
# Primary key detection
# ---------------------------------------------------------------------------

def test_field_pk_alias():
    class Foo(Model):
        id: str = Field(pk=True)

    assert Foo.__pk__ == "id"


def test_field_primary_alias():
    class Foo(Model):
        id: str = Field(primary=True)

    assert Foo.__pk__ == "id"


def test_field_primary_key_alias():
    class Foo(Model):
        id: str = Field(primary_key=True)

    assert Foo.__pk__ == "id"


def test_double_pks():
    with pytest.raises(ModelIntegrityError):
        class Book(Model):
            id: int = Field(pk=True)
            name: str = Field(pk=True)


# ---------------------------------------------------------------------------
# Schema generation
# ---------------------------------------------------------------------------

binary_data = b"some weird data"


class Complex(Model):
    id: int = Field(pk=True, auto=True)
    created: datetime = Field(auto=True)
    name: str = "me"
    lastname: str | None = None
    foo: str
    data: bytes = binary_data


def test_complex_model_schema():
    expected = (
        "CREATE TABLE IF NOT EXISTS complex(\n"
        "\r    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "\r    created DATETIME DEFAULT CURRENT_TIMESTAMP,\n"
        "\r    name TEXT DEFAULT 'me',\n"
        "\r    lastname TEXT,\n"
        "\r    foo TEXT NOT NULL,\n"
        f"\r    data BLOB DEFAULT (X'{binary_data.hex()}')\n"
        ");"
    )
    assert Complex.__schema__.strip() == expected.strip()


def test_complex_schema_works():
    db = Path(__file__).parent / "db.sqlite3"
    db.unlink(missing_ok=True)
    try:
        con = sqlite3.connect(db)
        con.execute(Complex.__schema__)
        con.commit()
    finally:
        con.close()
        db.unlink(missing_ok=True)


class User(Model):
    id: int = Field(primary=True)
    name: str


def test_user_schema():
    expected = """
CREATE TABLE IF NOT EXISTS user(
\r    id INTEGER PRIMARY KEY,
\r    name TEXT NOT NULL
);
"""
    assert User.__schema__.strip() == expected.strip()


def test_pk():
    assert User.__pk__ == "id"


def test_int_pk_auto():
    class Foo(Model):
        id: int = Field(pk=True, auto=True)

    assert "id INTEGER PRIMARY KEY AUTOINCREMENT" in Foo.__schema__


def test_field_unique_schema():
    class Foo(Model):
        id: int = Field(pk=True)
        email: str = Field(unique=True)

    assert "email TEXT NOT NULL UNIQUE" in Foo.__schema__


# ---------------------------------------------------------------------------
# ModelIntegrityError paths
# ---------------------------------------------------------------------------

def test_unsupported_field_type():
    with pytest.raises(ModelIntegrityError):
        class Bad(Model):
            tags: list


def test_unique_with_default_raises():
    with pytest.raises(ModelIntegrityError):
        class Bad(Model):
            name: str = Field(unique=True, default="foo")


# ---------------------------------------------------------------------------
# ForeignField errors
# ---------------------------------------------------------------------------

def test_foreign_field_type_error():
    with pytest.raises(TypeError):
        ForeignField(references=str)


def test_foreign_field_no_pk_error():
    class NoPk(Model):
        name: str

    with pytest.raises(ValueError):
        ForeignField(references=NoPk)


# ---------------------------------------------------------------------------
# SQLite type mapping in schema
# ---------------------------------------------------------------------------

def test_bool_schema():
    class Flags(Model):
        id: int = Field(pk=True)
        active: bool

    assert "active INTEGER NOT NULL" in Flags.__schema__


def test_float_schema():
    class Scores(Model):
        id: int = Field(pk=True)
        value: float

    assert "value REAL NOT NULL" in Scores.__schema__


def test_date_schema():
    class Events(Model):
        id: int = Field(pk=True)
        event_date: date

    assert "event_date DATE NOT NULL" in Events.__schema__


def test_time_schema():
    class Schedules(Model):
        id: int = Field(pk=True)
        start_time: time

    assert "start_time TIME NOT NULL" in Schedules.__schema__


def test_auto_date_schema():
    class Log(Model):
        id: int = Field(pk=True, auto=True)
        logged_on: date = Field(auto=True)

    assert "logged_on DATE DEFAULT CURRENT_DATE" in Log.__schema__


def test_auto_time_schema():
    class Log(Model):
        id: int = Field(pk=True, auto=True)
        logged_at: time = Field(auto=True)

    assert "logged_at TIME DEFAULT CURRENT_TIME" in Log.__schema__
