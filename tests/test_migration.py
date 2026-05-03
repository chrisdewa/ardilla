from pathlib import Path
from typing import Optional
from functools import partial
from contextlib import contextmanager

import pytest

from ardilla import Field, Model, Engine
from ardilla.errors import MigrationError
from ardilla.migration import generate_migration_script


db = Path(__file__).parent / "test_db.sqlite3"
unlink_db = partial(db.unlink, missing_ok=True)
engine = Engine(db)


@contextmanager
def clean_db():
    unlink_db()
    yield
    unlink_db()


# ---------------------------------------------------------------------------
# Happy-path migrations
# ---------------------------------------------------------------------------

def test_tablename_change():
    with clean_db():
        class A(Model):
            field: str

        with engine:
            crud = engine.crud(A)
            crud.insert(field="something")

        class B(Model):
            field: str

        script = generate_migration_script(A, B, original_tablename="a", new_tablename="b")

        con = engine.get_connection()
        con.executescript(script)
        con.commit()

        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cursor.fetchall()
        cursor.close()
        con.close()

        assert table_names[0]["name"] == "b"


def test_full_migration():
    """table rename + drop column + add column + type change."""
    with clean_db():
        class OldUser(Model):
            __tablename__ = "user"
            id: int = Field(pk=True, auto=True)
            name: str
            age: str
            glam: str = "bling"

        with engine:
            crud = engine.crud(OldUser)
            users = [OldUser(name=f"user {n}", age=str(n)) for n in range(100)]
            crud.save_many(*users)

        class NewUser(Model):
            __tablename__ = "users"
            id: int = Field(pk=True, auto=True)
            name: str
            age: int = 0
            pet: Optional[str]

        script = generate_migration_script(
            OldUser, NewUser, original_tablename="user", new_tablename="users"
        )

        con = engine.get_connection()
        con.executescript(script)
        con.commit()
        con.close()

        with engine:
            crud = engine.crud(NewUser)
            crud.insert(name="chris", age=35, pet="liu")


def test_migration_no_rename():
    """Migration without a tablename change (new_tablename omitted)."""
    with clean_db():
        class UserV1(Model):
            __tablename__ = "userv"
            id: int = Field(pk=True, auto=True)
            name: str

        with engine:
            crud = engine.crud(UserV1)
            crud.insert(name="chris")

        class UserV2(Model):
            __tablename__ = "userv"
            id: int = Field(pk=True, auto=True)
            name: str
            bio: Optional[str]

        script = generate_migration_script(UserV1, UserV2, original_tablename="userv")

        con = engine.get_connection()
        con.executescript(script)
        con.commit()
        con.close()

        with engine:
            crud = engine.crud(UserV2)
            assert crud.count() == 1
            assert crud.get_or_none(name="chris") is not None


# ---------------------------------------------------------------------------
# MigrationError paths
# ---------------------------------------------------------------------------

def test_migration_error_unique_field():
    """Adding a UNIQUE column to an existing table is not scriptable."""
    class OldM(Model):
        name: str

    class NewM(Model):
        name: str
        email: str = Field(unique=True)

    with pytest.raises(MigrationError):
        generate_migration_script(OldM, NewM, original_tablename="oldm")


def test_migration_error_pk_field():
    """Adding a PRIMARY KEY column to an existing table is not scriptable."""
    class OldM(Model):
        name: str

    class NewM(Model):
        name: str
        id: int = Field(pk=True)

    with pytest.raises(MigrationError):
        generate_migration_script(OldM, NewM, original_tablename="oldm")


def test_migration_error_not_null_no_default():
    """Adding a NOT NULL column without a default is not scriptable."""
    class OldM(Model):
        name: str

    class NewM(Model):
        name: str
        age: int  # required, NOT NULL, no default

    with pytest.raises(MigrationError):
        generate_migration_script(OldM, NewM, original_tablename="oldm")
