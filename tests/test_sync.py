
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from ardilla import Engine, Model, Crud


path = Path(__file__).parent
db = path / 'testdb.sqlite' 

class User(Model):
    id: int
    name: str
    age: int

@contextmanager
def cleanup():
    try:
        db.unlink(missing_ok=True)
        engine = Engine(db)
        Crud.engine = engine
        crud: Crud[User] = Crud(User)
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


def test_create():
    with cleanup() as crud:
        chris = User(id=1, name='chris', age=35)
        moni = User(id=2, name='moni', age=36)
        elena = User(id=3, name='elena', age=5)
        crud.save_many(chris, moni, elena)
        fran = User(id=4, name='fran', age=1)
        crud.save_one(fran)
        
        with query() as cur:
            cur.execute('SELECT * FROM user;')
            res = cur.fetchall()
        
        assert len(res) == 4, 'Mistmatch created vs found'

def test_read():
    with cleanup() as crud:
        chris = User(id=1, name='chris', age=35)
        chris2 = User(id=2, name='chris', age=36)
        elena = User(id=3, name='elena', age=5)
        crud.save_many(chris, chris2, elena)
        
        users = crud.get_all()
        assert len(users) == 3, 'Wrong number of read users from get_all'
        users = crud.get_many(name='chris')
        assert len(users) == 2, 'wrong number of users from get_many'
        u = crud.get_or_none(id=1)
        assert u == chris, 'bad user found'
        u = crud.get_or_none(id=5)
        assert u is None, 'bad user not found'
        u,c = crud.get_or_create(name='fran', age=1)
        assert c is True, 'Bad created value'
        assert u == User(id=4, name='fran', age=1), 'bad created user'
        u,c = crud.get_or_create(id=3)
        assert u == elena, 'bad user found'
        assert c is False, 'Bad not created value'

def test_update():
    with cleanup() as crud:
        chris = User(id=1, name='chris', age=35)
        moni = User(id=2, name='moni', age=36)
        crud.save_many(chris, moni)
        chris.age = 40
        crud.save_one(chris)
        u = crud.get_or_none(**chris.dict())
        assert u is not None, 'user not updated'
        chris.age = 45
        moni.age = 50
        crud.save_many(chris, moni)
        u = crud.get_or_none(**moni.dict())
        assert u is not None, 'User not updated on many'

def test_delete():
    with cleanup() as crud:
        chris = User(id=1, name='chris', age=35)
        moni = User(id=2, name='moni', age=36)
        elena = User(id=3, name='elena', age=5)
        crud.save_many(chris, moni, elena)
        crud.delete_one(moni)
        users = crud.get_all()
        assert len(users) == 2, "Delete one missmatch"
        crud.delete_many(chris, elena)
        users = crud.get_all()
        assert len(users) == 0, "Delete many missmatch"