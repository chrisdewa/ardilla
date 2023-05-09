from ardilla.models import Model

class User(Model):
    id: int
    name: str

tablename = 'user'
schema = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
"""

def test_default_tablename():
    assert User.__tablename__ == 'user', f'wrong default tablename {User.__tablename__} != {tablename}'

def test_defaul_schema():
    assert User.__schema__.strip() == schema.strip()

