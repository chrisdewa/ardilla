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
    ...

"""
Abstract methods:
    save_one x
    save_many x
    get_all x
    get_many x
    get_or_create x
    get_or_none x 
    delete_one x
    delete_many x
"""
