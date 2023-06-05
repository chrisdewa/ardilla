import random
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from functools import partial


from ardilla import Engine, Model, Crud
from ardilla.errors import QueryExecutionError, DisconnectedEngine
from pydantic import Field

from ardilla.fields import ForeignField


path = Path(__file__).parent
db = path / "test_sync.sqlite"

unlinkdb = partial(db.unlink, missing_ok=True)

@contextmanager
def cleanup():
    unlinkdb()
    try:
        yield
    finally:
        unlinkdb()

class User(Model):
    id: int = Field(pk=True, auto=True)
    name: str

def test_context_engine():
    with cleanup():
        try:
            with Engine(db) as engine:
                crud = engine.crud(User)
                u = crud.insert(name='chris') # should pass
                assert u.name == 'chris'
            crud.insert(name='moni')
        except Exception as e:
            assert isinstance(e, DisconnectedEngine), f'Wrong exception raised'

def test_st_engine():
    unlinkdb()
    try:
        engine = Engine(db)
        engine.connect()
        crud = engine.crud(User)
        u = crud.insert(name='chris') # should pass
        assert u.name == 'chris'
        engine.close()
        crud.insert(name='moni')
    except Exception as e:
        assert isinstance(e, DisconnectedEngine), f'Wrong exception raised'
    finally:
        engine.close()
        unlinkdb()


# CREATE

def test_insert():
   with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        u = crud.insert(name="chris")
        
        assert u is not None, "User wasn't created as expected"
        assert u.__rowid__ is not None, "Created user did not have __rowid__ set"
        assert u.__rowid__ == 1, "Created User did not have correct __rowid__ "
        try:
            crud.insert(id=1, name="chris")
        except Exception as err:
            assert isinstance(err, QueryExecutionError), f'Wrong error rised: {err}'
        else:
            raise Exception("QueryExcecutionError should have been rised")


def test_insert_or_ignore():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        kws = dict(id=1, name='chris')
        u1 = crud.insert(**kws)
        u2= crud.insert_or_ignore(**kws)
        
        assert u2 is None

def test_save_one():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        u = crud.insert(name='chris')
        u.name = 'alex'
        crud.save_one(u)
        
        user = crud.get_or_none(name='alex')
        assert user.id == 1


def test_save_many():
    users = [User(name=f'user {n}') for n in range(20)]
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        crud.save_many(*users)

        assert crud.count() == 20

# READ
def test_get_all():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for n in range(10):
            crud.insert(name=f'user {n}')

        total = crud.count()
        assert total == 10

def test_get_many():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        names = ['chris', 'moni', 'elena', 'fran']
        for name in names:
            for _ in range(3):
                crud.insert(name=name)
        
        chrises = crud.count(name='chris')
        
        assert chrises == 3

def test_get_or_create():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        chris, created = crud.get_or_create(name='chris')
        assert chris.id == 1
        assert created is True
        chris, created = crud.get_or_create(name='chris')
        assert chris.id == 1
        assert created is False

def test_get_or_none():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        chris = crud.get_or_none(name='chris')
        assert chris is None
        crud.insert(name='chris')
        chris = crud.get_or_none(name='chris')
        assert chris is not None

def test_delete_one():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        chrises = [User(name='chris') for _ in range(10)]
        crud.save_many(*chrises)
        
        x = User(id=5, name='chris')
        crud.delete_one(x)
        
        users = crud.get_all()
        assert len(users) == 9
        assert all(u.id != 5 for u in users)


def test_delete_many():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        users = [
            User(id=n, name='chris') for n in range(10)
        ]
        crud.save_many(*users)
        
        to_delete = users[:-1]
        crud.delete_many(*to_delete)
        
        users = crud.get_all()
        assert len(users) == 1, "Delete many didn't delete the correct amount of users"


def test_foreign_keys():
    db = path / 'sync_test.sqlite'
    db.unlink(missing_ok=True)
    engine = Engine(db, enable_foreing_keys=True)
    engine.connect()
    
    class Guild(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        
    class User(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        guild_id: int = ForeignField(references=Guild, on_delete=ForeignField.CASCADE)
    
    gcrud = engine.crud(Guild)
    ucrud = engine.crud(User)
    
    ga = gcrud.insert(name='guild a')
    gb = gcrud.insert(name='guild b')
    for guild in [ga, gb]:
        for n in range(5):
            ucrud.insert(name=f'user {n}', guild_id=guild.id)
    
    assert ucrud.count() == 10
    gcrud.delete_one(ga)
    assert ucrud.count() == 5 
    engine.close()
    db.unlink(missing_ok=True)



