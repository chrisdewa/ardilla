
from contextlib import asynccontextmanager
from pathlib import Path
from functools import partial

import pytest

from ardilla import Model, Field, ForeignField
from ardilla.asyncio import Engine
from ardilla.errors import QueryExecutionError, DisconnectedEngine




path = Path(__file__).parent
db = path / "test_sync.sqlite"

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


@pytest.mark.asyncio
async def test_context_engine():
    async with cleanup():
        try:
            async with Engine(db) as engine:
                crud = await engine.crud(User)
                u = await crud.insert(name='chris') # should pass
                assert u.name == 'chris'
            await crud.insert(name='moni')
        except Exception as e:
            assert isinstance(e, DisconnectedEngine), f'Wrong exception raised'

@pytest.mark.asyncio
async def test_st_engine():
    unlinkdb()
    try:
        engine = Engine(db)
        await engine.connect()
        crud = await engine.crud(User)
        u = await crud.insert(name='chris') # should pass
        assert u.name == 'chris'
        await engine.close()
        await crud.insert(name='moni')
    except Exception as e:
        assert isinstance(e, DisconnectedEngine), f'Wrong exception raised'
    finally:
        await engine.close()
        unlinkdb()


# CREATE

@pytest.mark.asyncio
async def test_insert():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        u = await crud.insert(name="chris")
        
        assert u is not None, "User wasn't created as expected"
        assert u.__rowid__ is not None, "Created user did not have __rowid__ set"
        assert u.__rowid__ == 1, "Created User did not have correct __rowid__ "
        try:
            await crud.insert(id=1, name="chris")
        except Exception as err:
            assert isinstance(err, QueryExecutionError), f'Wrong error rised: {err}'
        else:
            raise Exception("QueryExcecutionError should have been rised")

@pytest.mark.asyncio
async def test_insert_or_ignore():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        kws = dict(id=1, name='chris')
        await crud.insert(**kws)
        u2 = await crud.insert_or_ignore(**kws)
        
        assert u2 is None


@pytest.mark.asyncio
async def test_save_one():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        u = await crud.insert(name='chris')
        u.name = 'alex'
        await crud.save_one(u)
        
        user = await crud.get_or_none(name='alex')
        assert user.id == 1

@pytest.mark.asyncio
async def test_save_many():
    users = [User(name=f'user {n}') for n in range(20)]
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        await crud.save_many(*users)

        assert await crud.count() == 20

# READ
@pytest.mark.asyncio
async def test_get_all():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        for n in range(10):
            await crud.insert(name=f'user {n}')

        assert await crud.count() == 10

@pytest.mark.asyncio
async def test_get_many():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        names = ['chris', 'moni', 'elena', 'fran']
        for name in names:
            for _ in range(3):
                await crud.insert(name=name)
                
        assert await crud.count(name='chris') == 3

@pytest.mark.asyncio
async def test_get_or_create():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        chris, created = await crud.get_or_create(name='chris')
        assert chris.id == 1
        assert created is True
        chris, created = await crud.get_or_create(name='chris')
        assert chris.id == 1
        assert created is False

@pytest.mark.asyncio
async def test_get_or_none():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        chris = await crud.get_or_none(name='chris')
        assert chris is None
        await crud.insert(name='chris')
        chris = await crud.get_or_none(name='chris')
        assert chris is not None

@pytest.mark.asyncio
async def test_delete_one():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        chrises = [User(name='chris') for _ in range(10)]
        await crud.save_many(*chrises)
        
        x = User(id=5, name='chris')
        await crud.delete_one(x)
        
        users = await crud.get_all()
        assert len(users) == 9
        assert all(u.id != 5 for u in users)

@pytest.mark.asyncio
async def test_delete_many():
    async with cleanup(), Engine(db) as engine:
        crud = await engine.crud(User)
        users = [
            User(id=n, name='chris') for n in range(10)
        ]
        await crud.save_many(*users)
        
        to_delete = users[:-1]
        await crud.delete_many(*to_delete)
        
        assert await crud.count() == 1, "Delete many didn't delete the correct amount of users"

@pytest.mark.asyncio
async def test_foreign_keys():
    db = path / 'sync_test.sqlite'
    db.unlink(missing_ok=True)
    engine = Engine(db, enable_foreing_keys=True)
    await engine.connect()
    
    class Guild(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        
    class User(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        guild_id: int = ForeignField(references=Guild, on_delete=ForeignField.CASCADE)
    
    gcrud = await engine.crud(Guild)
    ucrud = await engine.crud(User)
    
    ga = await gcrud.insert(name='guild a')
    gb = await gcrud.insert(name='guild b')
    for guild in [ga, gb]:
        for n in range(5):
            await ucrud.insert(name=f'user {n}', guild_id=guild.id)
    
    assert await ucrud.count() == 10
    await gcrud.delete_one(ga)
    assert await ucrud.count() == 5 
    await engine.close()
    db.unlink(missing_ok=True)

