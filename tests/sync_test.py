from pathlib import Path
from ardilla import Engine, Model, Crud


path = Path(__file__).parent
db = path / 'testdb.sqlite' 

db.unlink(missing_ok=True)    

engine = Engine(db)

Crud.engine = engine
class User(Model):
    id: int
    name: str
    age: int

crud: Crud[User] = Crud(User)

def test():
    print('setting up database')
    engine.setup()
    print('running tests')
    chris = User(id=1, name='chris', age=35)
    moni = User(id=2, name='moni', age=36)
    elena = User(id=3, name='elena', age=5)
    
    crud.save_many(chris, moni, elena)
    print('save many works')
    u = crud.get_or_none(id=4)
    assert u is None
    print('get_or_none works')
    u,created = crud.get_or_create(id=4, name='fran', age=1)
    print(u, created)
    assert u is not None
    assert created is True
    u,created = crud.get_or_create(id=4, name='fran', age=1)
    assert u is not None
    assert created is False
    print(u, created)
    print('get or create works')
    alt_elena = User(id=5, name='elena', age=6)
    crud.save_one(alt_elena)
    users = crud.get_many(name='elena')
    assert len(users) == 2
    print('save one works')
    crud.delete_one(alt_elena)
    users = crud.get_all()
    assert len(users) == 4
    print('delete one works')
    crud.delete_many(chris, moni)
    users = crud.get_all()
    assert len(users) == 2
    print('delete many works')
    print('everything ok')
    print('cleaning up')
    db.unlink(missing_ok=True)