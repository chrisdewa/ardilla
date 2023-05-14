import sqlite3
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path

import pytest

from pydantic import Field

from ardilla import Model
from ardilla.asyncio import Engine, Crud
from ardilla.errors import QueryExecutionError


path = Path(__file__).parent
db = path / "testdb.sqlite"


class User(Model):
    id: int = Field(primary=True)
    name: str
    age: int


@asynccontextmanager
async def cleanup():
    try:
        db.unlink(missing_ok=True)
        engine = Engine(db)
        crud = engine.crud(User)
        await engine.setup()
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


@pytest.mark.asyncio
async def test_insert():
    async with cleanup() as crud:
        u = await crud.insert(id=1, name="chris", age=35)
        assert u is not None, "User wasn't created as expected"

        try:
            await crud.insert(id=1, name="chris", age=35)
        except QueryExecutionError:
            pass
        else:
            raise Exception("QueryExcecutionError should have been rised")


@pytest.mark.asyncio
async def test_insert_or_ignore():
    async with cleanup() as crud:
        u = await crud.insert_or_ignore(id=1, name="chris", age=35)
        assert u is not None, "User wasn't created as expected"
        u = await crud.insert_or_ignore(id=1, name="chris", age=35)
        assert u is None, "User was returned but it should have been None"


@pytest.mark.asyncio
async def test_save_one():
    async with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        await crud.save_one(chris)

        with query() as cur:
            cur.execute("SELECT * FROM user;")
            res = cur.fetchall()

        assert len(res) == 1, "Incorrect number of users in the database"


@pytest.mark.asyncio
async def test_save_many():
    async with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        moni = User(id=2, name="moni", age=36)
        elena = User(id=3, name="elena", age=5)
        await crud.save_many(chris, moni, elena)

        with query() as cur:
            cur.execute("SELECT * FROM user;")
            res = cur.fetchall()

        assert len(res) == 3, "Incorrect number of users in the database"


@pytest.mark.asyncio
async def test_get_all():
    async with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        moni = User(id=2, name="moni", age=36)
        elena = User(id=3, name="elena", age=5)
        await crud.save_many(chris, moni, elena)

        users = await crud.get_all()
        assert len(users) == 3, "Incorrect number of users returned"


@pytest.mark.asyncio
async def test_get_many():
    async with cleanup() as crud:
        u1 = User(id=1, name="chris", age=35)
        u2 = User(id=2, name="chris", age=35)
        u3 = User(id=3, name="chris", age=35)
        u4 = User(id=4, name="moni", age=34)
        u5 = User(id=5, name="fran", age=1)
        await crud.save_many(u1, u2, u3, u4, u5)

        users = await crud.get_many(name="chris")

        assert len(users) == 3, "Incorrect number of users returned"


@pytest.mark.asyncio
async def test_get_or_create():
    async with cleanup() as crud:
        elena = User(id=1, name="elena", age=5)
        await crud.save_one(elena)

        u, c = await crud.get_or_create(name="fran", age=1)
        assert c is True, "User should have been created"
        assert u == User(id=2, name="fran", age=1), f"Unexpected user was created: {u}"
        u, c = await crud.get_or_create(id=1)
        assert u == elena, "Mismatch between expected and returned user"
        assert c is False, "User shouldn't have been created"


@pytest.mark.asyncio
async def test_get_or_none():
    async with cleanup() as crud:
        elena = User(id=1, name="elena", age=5)
        await crud.save_one(elena)

        u = await crud.get_or_none(id=1)
        assert u is not None, "User wasn't found but it should have"
        u = await crud.get_or_none(id=2)
        assert u is None, "User shouln't have been found but was"


@pytest.mark.asyncio
async def test_delete_one():
    async with cleanup() as crud:
        chris = User(id=1, name="chris", age=35)
        moni = User(id=2, name="moni", age=36)
        elena = User(id=3, name="elena", age=5)
        await crud.save_many(chris, moni, elena)
        await crud.delete_one(moni)
        users = await crud.get_all()
        assert len(users) == 2, "Delete one didn't delete the correct amount of users"

class Foo(Model):
    a: str
    b: int

@pytest.mark.asyncio
async def test_delete_one_without_ids():
    db.unlink(missing_ok=True)
    engine = Engine(db)
    crud = engine.crud(Foo)
    try:
        for i, l in enumerate('abcdef',1):
            await crud.insert(a=l, b=i)
            
        to_del = [
            Foo(a='b', b=2),
            Foo(a='c', b=3),
            Foo(a='d', b=4),
        ]
        for obj in to_del:
            await crud.delete_one(obj)
        
        foos = await crud.get_all()
        assert len(foos) == 3, 'Mismatch beween expected and found after delete_many'
        
    finally:
        db.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_delete_many_by_id():
    async with cleanup() as crud:
        users = [
            User(id=n, name='chris', age=n)
            for n in range(10)
        ]
        await crud.save_many(*users)
        
        to_delete = users[:-1]
        await crud.delete_many(*to_delete)
        
        users = await crud.get_all()
        assert len(users) == 1, "Delete many didn't delete the correct amount of users"

@pytest.mark.asyncio
async def test_delete_many_by_rowid():
    async with cleanup() as crud:
        users = [
            User(id=n, name='chris', age=n)
            for n in range(10)
        ]
        await crud.save_many(*users)
       
        await crud.delete_many(*users[:-1])
        
        users = await crud.get_all()
        
        
        assert len(users) == 1, "Delete many didn't delete the correct amount of users"

