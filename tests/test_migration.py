
from pathlib import Path
from typing import Optional
from functools import partial
from contextlib import contextmanager

from ardilla import Field, Model, Engine
from ardilla.migration import generate_migration_script

db = Path(__file__).parent / 'test_db.sqlite3'
unlink_db = partial(db.unlink, missing_ok=True)
engine = Engine(db)

@contextmanager
def clean_db():
    unlink_db()
    yield
    unlink_db()


def test_tablename_change():
    with clean_db():
        class A(Model):
            field: str
        
        with engine:
            crud = engine.crud(A)
            crud.insert(field='something')
        
        class B(Model):
            field: str

        script = generate_migration_script(
            A, B, original_tablename='a', new_tablename='b'
        )

        con = engine.get_connection()
        con.executescript(script)
        con.commit()
        
        cursor = con.cursor()

        # Execute the query to get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        # Fetch all the table names
        table_names = cursor.fetchall()
        cursor.close()
        con.close()

        assert table_names[0]['name'] == 'b'



def test_full_migration():
    """
    Tests:
        - table rename
        - dropping columns
        - adding columns
        - changing column type
    """
    with clean_db():
        
        class User(Model):
            id: int = Field(pk=True, auto=True)
            name: str
            age: str
            glam: str = 'bling'
        
        with engine:
            crud = engine.crud(User)
            users = [User(name=f'user {n}', age=str(n)) for n in range(100)]
            crud.save_many(*users)

        class NewUser(Model):
            __tablename__ = 'users'
            id: int = Field(pk=True, auto=True)
            name: str
            age: int = 0
            pet: Optional[str]
        
        script = generate_migration_script(
            User, NewUser, original_tablename='user', new_tablename='users'
        )

        con = engine.get_connection()
        con.executescript(script)
        con.commit()
        con.close()

        with engine:
            crud = engine.crud(NewUser)
            crud.insert(name='chris', age=35, pet='liu')
        
        db.unlink(missing_ok=True)
        







