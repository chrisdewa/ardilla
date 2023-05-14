import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest

from ardilla import Engine, Model, Crud
from ardilla.errors import QueryExecutionError
from pydantic import Field


path = Path(__file__).parent
db = path / "testdb.sqlite"


class User(Model):
    id: int = Field(primary=True, autoincrement=True)
    name: str
    age: int


@contextmanager
def cleanup():
    try:
        db.unlink(missing_ok=True)
        engine = Engine(db)
        crud = engine.crud(User)
        engine.setup()
        yield crud
    finally:
        db.unlink(missing_ok=True)


@contextmanager
def query():
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        yield cur
    finally:
        cur.close()
        con.close()


"""
Abstract methods:
    insert x
    insert_or_ignore x
    save_one x
    save_many x
    get_all x
    get_many x
    get_or_create x
    get_or_none x 
    delete_one x
    delete_many x
"""


def test_insert():
    with cleanup() as crud:
        u = crud.insert(id=1, name="chris", age=35)
        assert u is not None, "User wasn't created as expected"
        assert u.__rowid__ is not None, "Created user did not have __rowid__ set"
        assert u.__rowid__ == 1, "Created User did not have correct __rowid__ "
        try:
            crud.insert(id=1, name="chris", age=35)
        except QueryExecutionError:
            pass
        else:
            raise Exception("QueryExcecutionError should have been rised")


def test_insert_or_ignore():
    with cleanup() as crud:
        u = crud.insert_or_ignore(id=1, name="chris", age=35)
        assert u is not None, "User wasn't created as expected"
        u = crud.insert_or_ignore(id=1, name="chris", age=35)
        assert u is None, "User was returned but it should have been None"


def test_save_one():
    with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        crud.save_one(chris)

        with query() as cur:
            cur.execute("SELECT * FROM user;")
            res = cur.fetchall()

        assert len(res) == 1, "Incorrect number of users in the database"


def test_save_one_rowid():
    with cleanup() as crud:
        chris = crud.insert(id=1, name="chris", age=35)
        chris.name = 'chris_is_alt'
        crud.save_one(chris)
        

        with query() as cur:
            cur.execute("SELECT * FROM user;")
            res = cur.fetchall()

        assert len(res) == 1, "Incorrect number of users in the database"

def test_save_many():
    with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        moni = User(id=2, name="moni", age=36)
        elena = User(id=3, name="elena", age=5)
        crud.save_many(chris, moni, elena)

        with query() as cur:
            cur.execute("SELECT * FROM user;")
            res = cur.fetchall()

        assert len(res) == 3, "Incorrect number of users in the database"


def test_get_all():
    with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        moni = User(id=2, name="moni", age=36)
        elena = User(id=3, name="elena", age=5)
        crud.save_many(chris, moni, elena)

        users = crud.get_all()
        assert len(users) == 3, "Incorrect number of users returned"


def test_get_many():
    with cleanup() as crud:
        u1 = User(id=1, name="chris", age=35)
        u2 = User(id=2, name="chris", age=35)
        u3 = User(id=3, name="chris", age=35)
        u4 = User(id=4, name="moni", age=34)
        u5 = User(id=5, name="fran", age=1)
        crud.save_many(u1, u2, u3, u4, u5)

        users = crud.get_many(name="chris")

        assert len(users) == 3, "Incorrect number of users returned"
        assert all(u.__rowid__ for u in users), 'User objects did not get their rowid populated'


def test_get_or_create():
    with cleanup() as crud:
        elena = User(id=1, name="elena", age=5)
        crud.save_one(elena)

        u, c = crud.get_or_create(name="fran", age=1)
        assert c is True, "User should have been created"
        assert u == User(id=2, name="fran", age=1), f"Unexpected user was created: {u}"
        u, c = crud.get_or_create(id=1)
        assert u == elena, "Mismatch between expected and returned user"
        assert c is False, "User shouldn't have been created"


def test_get_or_none():
    with cleanup() as crud:
        elena = User(id=1, name="elena", age=5)
        crud.save_one(elena)

        u = crud.get_or_none(id=1)
        assert u is not None, "User wasn't found but it should have"
        u = crud.get_or_none(id=2)
        assert u is None, "User shouln't have been found but was"


def test_delete_one():
    with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        moni = User(id=2, name="moni", age=36)
        elena = User(id=3, name="elena", age=5)
        crud.save_many(chris, moni, elena)
        crud.delete_one(moni)
        users = crud.get_all()
        assert len(users) == 2, "Delete one didn't delete the correct amount of users"


def test_delete_many_by_id():
    with cleanup() as crud:
        users = [
            User(id=n, name='chris', age=n)
            for n in range(10)
        ]
        crud.save_many(*users)
        
        to_delete = users[:-1]
        crud.delete_many(*to_delete)
        
        users = crud.get_all()
        assert len(users) == 1, "Delete many didn't delete the correct amount of users"


def test_delete_many_by_rowid():
    with cleanup() as crud:
        users = [
            User(id=n, name='chris', age=n)
            for n in range(10)
        ]
        crud.save_many(*users)
       
        crud.delete_many(*users[:-1])
        
        users = crud.get_all()
        
        
        assert len(users) == 1, "Delete many didn't delete the correct amount of users"

