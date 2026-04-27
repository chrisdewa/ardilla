from contextlib import asynccontextmanager
from pathlib import Path
from functools import partial

import pytest

from ardilla import Model, Field, ForeignField
from ardilla.asyncio import Engine
from ardilla.errors import BadQueryError, QueryExecutionError, DisconnectedEngine


path = Path(__file__).parent
db = path / "test_async.sqlite"

unlinkdb = partial(db.unlink, missing_ok=True)


@asynccontextmanager
async def cleanup():
    unlinkdb()
    try:
        yield
    finally:
        unlinkdb()


class User(Model):
    id: int = Field(pk=True, auto=True)
    name: str


# ---------------------------------------------------------------------------
# Engine lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_context_engine():
    async with cleanup():
        try:
            async with Engine(db) as engine:
                crud = await engine.crud(User)
                u = await crud.insert(name="chris")
                assert u.name == "chris"
            await crud.insert(name="moni")
        except Exception as e:
            assert isinstance(e, DisconnectedEngine), f"Wrong exception raised: {e}"


@pytest.mark.asyncio
async def test_st_engine():
    unlinkdb()
    try:
        engine = Engine(db)
        await engine.connect()
        crud = await engine.crud(User)
        u = await crud.insert(name="chris")
        assert u.name == "chris"
        await engine.close()
        await crud.insert(name="moni")
    except Exception as e:
        assert isinstance(e, DisconnectedEngine), f"Wrong exception raised: {e}"
    finally:
        await engine.close()
        unlinkdb()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_insert():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        u = await crud.insert(name="chris")
        assert u is not None
        assert u.__rowid__ is not None
        assert u.__rowid__ == 1
        with pytest.raises(QueryExecutionError):
            await crud.insert(id=1, name="chris")


@pytest.mark.asyncio
async def test_insert_or_ignore():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        # Success: no conflict — returns the new object
        u1 = await crud.insert_or_ignore(name="chris")
        assert u1 is not None
        assert u1.name == "chris"
        # Conflict: returns None
        u2 = await crud.insert_or_ignore(id=u1.id, name="chris")
        assert u2 is None


@pytest.mark.asyncio
async def test_save_one():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        u = await crud.insert(name="chris")
        u.name = "alex"
        await crud.save_one(u)
        user = await crud.get_or_none(name="alex")
        assert user.id == 1


@pytest.mark.asyncio
async def test_save_one_no_rowid():
    """INSERT OR REPLACE path: object constructed directly, __rowid__ is None."""
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        u = User(id=42, name="chris")
        assert u.__rowid__ is None
        await crud.save_one(u)
        found = await crud.get_or_none(id=42)
        assert found is not None
        assert found.name == "chris"


@pytest.mark.asyncio
async def test_save_many():
    users = [User(name=f"user {n}") for n in range(20)]
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        await crud.save_many(*users)
        assert await crud.count() == 20


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_all():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        for n in range(10):
            await crud.insert(name=f"user {n}")
        users = await crud.get_all()
        assert len(users) == 10
        assert all(isinstance(u, User) for u in users)


@pytest.mark.asyncio
async def test_get_many():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        for name in ["chris", "moni", "elena"]:
            for _ in range(3):
                await crud.insert(name=name)
        chrises = await crud.get_many(name="chris")
        assert len(chrises) == 3
        assert all(u.name == "chris" for u in chrises)


@pytest.mark.asyncio
async def test_get_many_order_by():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        for n in range(5):
            await crud.insert(name=f"user {n}")
        asc = await crud.get_many(order_by={"id": "ASC"})
        desc = await crud.get_many(order_by={"id": "DESC"})
        assert asc[0].id < asc[-1].id
        assert desc[0].id > desc[-1].id


@pytest.mark.asyncio
async def test_get_many_limit():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        for n in range(10):
            await crud.insert(name=f"user {n}")
        users = await crud.get_many(limit=3)
        assert len(users) == 3


@pytest.mark.asyncio
async def test_get_or_create():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        chris, created = await crud.get_or_create(name="chris")
        assert chris.id == 1
        assert created is True
        chris, created = await crud.get_or_create(name="chris")
        assert chris.id == 1
        assert created is False


@pytest.mark.asyncio
async def test_get_or_none():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        assert await crud.get_or_none(name="chris") is None
        await crud.insert(name="chris")
        assert await crud.get_or_none(name="chris") is not None


@pytest.mark.asyncio
async def test_count():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        for n in range(5):
            await crud.insert(name=f"user {n}")
        assert await crud.count() == 5


@pytest.mark.asyncio
async def test_count_column():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        for n in range(5):
            await crud.insert(name=f"user {n}")
        assert await crud.count("id") == 5
        assert await crud.count("name") == 5


@pytest.mark.asyncio
async def test_invalid_query_kwarg():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        with pytest.raises(KeyError):
            await crud.get_or_none(nonexistent="value")


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_one():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        chrises = [User(name="chris") for _ in range(10)]
        await crud.save_many(*chrises)
        await crud.delete_one(User(id=5, name="chris"))
        users = await crud.get_all()
        assert len(users) == 9
        assert all(u.id != 5 for u in users)


@pytest.mark.asyncio
async def test_delete_one_by_values():
    """Fallback path: no pk, no rowid — matches by all field values."""
    class Tag(Model):
        label: str
        color: str

    db_tag = path / "test_tags_async.sqlite"
    db_tag.unlink(missing_ok=True)
    try:
        async with Engine(db_tag) as engine:
            crud = await engine.crud(Tag)
            await crud.insert(label="red", color="#ff0000")
            await crud.insert(label="blue", color="#0000ff")

            t = Tag(label="red", color="#ff0000")
            assert not t.__pk__
            assert t.__rowid__ is None
            await crud.delete_one(t)

            remaining = await crud.get_all()
            assert len(remaining) == 1
            assert remaining[0].label == "blue"
    finally:
        db_tag.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_delete_many():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        users = [User(id=n, name="chris") for n in range(10)]
        await crud.save_many(*users)
        await crud.delete_many(*users[:-1])
        assert await crud.count() == 1


# ---------------------------------------------------------------------------
# Foreign keys
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_foreign_keys():
    db_fk = path / "async_test.sqlite"
    db_fk.unlink(missing_ok=True)
    engine = Engine(db_fk, enable_foreing_keys=True)
    await engine.connect()

    class Guild(Model):
        id: int = Field(pk=True, auto=True)
        name: str

    class Member(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        guild_id: int = ForeignField(references=Guild, on_delete=ForeignField.CASCADE)

    gcrud = await engine.crud(Guild)
    mcrud = await engine.crud(Member)

    ga = await gcrud.insert(name="guild a")
    gb = await gcrud.insert(name="guild b")
    for guild in [ga, gb]:
        for n in range(5):
            await mcrud.insert(name=f"member {n}", guild_id=guild.id)

    assert await mcrud.count() == 10
    await gcrud.delete_one(ga)
    assert await mcrud.count() == 5

    await engine.close()
    db_fk.unlink(missing_ok=True)
