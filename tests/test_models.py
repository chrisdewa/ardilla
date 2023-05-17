from ardilla.models import Model
from pydantic import Field


class User(Model):
    id: int = Field(primary=True)
    name: str


tablename = "user"
schema = """
CREATE TABLE IF NOT EXISTS user(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""


def test_default_tablename():
    assert (
        User.__tablename__ == "user"
    ), f"wrong default tablename {User.__tablename__} != {tablename}"


def test_default_schema():
    assert User.__schema__.strip() == schema.strip()


def test_pk():
    assert User.__pk__ == "id"
