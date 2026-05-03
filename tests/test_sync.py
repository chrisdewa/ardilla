from contextlib import contextmanager
from pathlib import Path
from functools import partial

import pytest

from datetime import date, time
from typing import Optional

from ardilla import Engine, Model, Field
from ardilla.errors import BadQueryError, QueryExecutionError, DisconnectedEngine
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


# ---------------------------------------------------------------------------
# Engine lifecycle
# ---------------------------------------------------------------------------

def test_context_engine():
    with cleanup():
        try:
            with Engine(db) as engine:
                crud = engine.crud(User)
                u = crud.insert(name="chris")
                assert u.name == "chris"
            crud.insert(name="moni")
        except Exception as e:
            assert isinstance(e, DisconnectedEngine), f"Wrong exception raised: {e}"


def test_st_engine():
    unlinkdb()
    try:
        engine = Engine(db)
        engine.connect()
        crud = engine.crud(User)
        u = crud.insert(name="chris")
        assert u.name == "chris"
        engine.close()
        crud.insert(name="moni")
    except Exception as e:
        assert isinstance(e, DisconnectedEngine), f"Wrong exception raised: {e}"
    finally:
        engine.close()
        unlinkdb()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_insert():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        u = crud.insert(name="chris")
        assert u is not None
        assert u.__rowid__ is not None
        assert u.__rowid__ == 1
        with pytest.raises(QueryExecutionError):
            crud.insert(id=1, name="chris")


def test_insert_or_ignore():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        # Success: no conflict — returns the new object
        u1 = crud.insert_or_ignore(name="chris")
        assert u1 is not None
        assert u1.name == "chris"
        # Conflict: returns None
        u2 = crud.insert_or_ignore(id=u1.id, name="chris")
        assert u2 is None


def test_insert_or_ignore_original_unchanged():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        original = crud.insert(name="alice")
        crud.insert_or_ignore(id=original.id, name="overwrite")
        fetched = crud.get_or_none(id=original.id)
        assert fetched.name == "alice"


def test_save_one():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        u = crud.insert(name="chris")
        u.name = "alex"
        crud.save_one(u)
        user = crud.get_or_none(name="alex")
        assert user.id == 1


def test_save_one_no_rowid():
    """INSERT OR REPLACE path: object constructed directly, __rowid__ is None."""
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        u = User(id=42, name="chris")
        assert u.__rowid__ is None
        crud.save_one(u)
        found = crud.get_or_none(id=42)
        assert found is not None
        assert found.name == "chris"


def test_save_many():
    users = [User(name=f"user {n}") for n in range(20)]
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        crud.save_many(*users)
        assert crud.count() == 20


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def test_get_all():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for n in range(10):
            crud.insert(name=f"user {n}")
        users = crud.get_all()
        assert len(users) == 10
        assert all(isinstance(u, User) for u in users)


def test_get_many():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for name in ["chris", "moni", "elena"]:
            for _ in range(3):
                crud.insert(name=name)
        chrises = crud.get_many(name="chris")
        assert len(chrises) == 3
        assert all(u.name == "chris" for u in chrises)


def test_get_many_order_by():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for n in range(5):
            crud.insert(name=f"user {n}")
        asc = crud.get_many(order_by={"id": "ASC"})
        desc = crud.get_many(order_by={"id": "DESC"})
        assert asc[0].id < asc[-1].id
        assert desc[0].id > desc[-1].id


def test_get_many_limit():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for n in range(10):
            crud.insert(name=f"user {n}")
        users = crud.get_many(limit=3)
        assert len(users) == 3


def test_get_many_order_by_and_limit():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for n in range(10):
            crud.insert(name=f"user {n}")
        results = crud.get_many(order_by={"id": "DESC"}, limit=3)
        assert len(results) == 3
        assert results[0].id > results[1].id > results[2].id


def test_get_or_create():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        chris, created = crud.get_or_create(name="chris")
        assert chris.id == 1
        assert created is True
        chris, created = crud.get_or_create(name="chris")
        assert chris.id == 1
        assert created is False


def test_get_or_create_returns_correct_values():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        obj, created = crud.get_or_create(name="zeus")
        assert created is True
        assert obj.name == "zeus"
        obj2, created2 = crud.get_or_create(name="zeus")
        assert created2 is False
        assert obj2.name == "zeus"
        assert obj2.id == obj.id


def test_get_or_none():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        assert crud.get_or_none(name="chris") is None
        crud.insert(name="chris")
        assert crud.get_or_none(name="chris") is not None


def test_count():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for n in range(5):
            crud.insert(name=f"user {n}")
        assert crud.count() == 5


def test_count_column():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for n in range(5):
            crud.insert(name=f"user {n}")
        assert crud.count("id") == 5
        assert crud.count("name") == 5


def test_count_with_filter():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for name in ["alice", "alice", "bob"]:
            crud.insert(name=name)
        assert crud.count(name="alice") == 2
        assert crud.count(name="bob") == 1


def test_count_column_with_filter():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        for name in ["alice", "alice", "bob"]:
            crud.insert(name=name)
        assert crud.count("id", name="alice") == 2


def test_invalid_query_kwarg():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        with pytest.raises(KeyError):
            crud.get_or_none(nonexistent="value")


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_one():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        chrises = [User(name="chris") for _ in range(10)]
        crud.save_many(*chrises)
        crud.delete_one(User(id=5, name="chris"))
        users = crud.get_all()
        assert len(users) == 9
        assert all(u.id != 5 for u in users)


def test_delete_one_by_values():
    """Fallback path: no pk, no rowid — matches by all field values."""
    class Tag(Model):
        label: str
        color: str

    db_tag = path / "test_tags.sqlite"
    db_tag.unlink(missing_ok=True)
    try:
        with Engine(db_tag) as engine:
            crud = engine.crud(Tag)
            crud.insert(label="red", color="#ff0000")
            crud.insert(label="blue", color="#0000ff")

            t = Tag(label="red", color="#ff0000")
            assert not t.__pk__
            assert t.__rowid__ is None
            crud.delete_one(t)

            remaining = crud.get_all()
            assert len(remaining) == 1
            assert remaining[0].label == "blue"
    finally:
        db_tag.unlink(missing_ok=True)


def test_delete_many():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        users = [User(id=n, name="chris") for n in range(10)]
        crud.save_many(*users)
        crud.delete_many(*users[:-1])
        remaining = crud.get_all()
        assert len(remaining) == 1


def test_save_many_empty_raises():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        with pytest.raises(BadQueryError):
            crud.save_many()


def test_delete_many_empty_raises():
    with cleanup(), Engine(db) as engine:
        crud = engine.crud(User)
        with pytest.raises(IndexError):
            crud.delete_many()


def test_delete_many_non_id_pk():
    """Regression: for_delete_many must use the actual pk column, not the hardcoded 'id'."""
    class Article(Model):
        slug: str = Field(pk=True)
        title: str

    db_article = path / "test_articles.sqlite"
    db_article.unlink(missing_ok=True)
    try:
        with Engine(db_article) as engine:
            crud = engine.crud(Article)
            a1 = crud.insert(slug="hello", title="Hello World")
            a2 = crud.insert(slug="world", title="World Post")
            crud.delete_many(a1, a2)
            assert crud.count() == 0
    finally:
        db_article.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Foreign keys
# ---------------------------------------------------------------------------

def test_foreign_keys():
    db_fk = path / "sync_test.sqlite"
    db_fk.unlink(missing_ok=True)
    engine = Engine(db_fk, enable_foreing_keys=True)
    engine.connect()

    class Guild(Model):
        id: int = Field(pk=True, auto=True)
        name: str

    class Member(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        guild_id: int = ForeignField(references=Guild, on_delete=ForeignField.CASCADE)

    gcrud = engine.crud(Guild)
    mcrud = engine.crud(Member)

    ga = gcrud.insert(name="guild a")
    gb = gcrud.insert(name="guild b")
    for guild in [ga, gb]:
        for n in range(5):
            mcrud.insert(name=f"member {n}", guild_id=guild.id)

    assert mcrud.count() == 10
    gcrud.delete_one(ga)
    assert mcrud.count() == 5

    engine.close()
    db_fk.unlink(missing_ok=True)


def test_foreign_keys_restrict():
    """RESTRICT prevents deleting a parent row when child rows reference it."""
    db_fk = path / "sync_restrict.sqlite"
    db_fk.unlink(missing_ok=True)
    engine = Engine(db_fk, enable_foreing_keys=True)
    engine.connect()

    class Category(Model):
        id: int = Field(pk=True, auto=True)
        name: str

    class Item(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        category_id: int = ForeignField(references=Category, on_delete=ForeignField.RESTRICT)

    ccrud = engine.crud(Category)
    icrud = engine.crud(Item)

    cat = ccrud.insert(name="electronics")
    icrud.insert(name="phone", category_id=cat.id)

    with pytest.raises(Exception):
        ccrud.delete_one(cat)

    assert icrud.count() == 1

    engine.close()
    db_fk.unlink(missing_ok=True)


def test_foreign_keys_set_null():
    """SET_NULL nulls the FK column on the child when the parent is deleted."""
    db_fk = path / "sync_set_null.sqlite"
    db_fk.unlink(missing_ok=True)
    engine = Engine(db_fk, enable_foreing_keys=True)
    engine.connect()

    class Team(Model):
        id: int = Field(pk=True, auto=True)
        name: str

    class Player(Model):
        id: int = Field(pk=True, auto=True)
        name: str
        team_id: Optional[int] = ForeignField(references=Team, on_delete=ForeignField.SET_NULL)

    tcrud = engine.crud(Team)
    pcrud = engine.crud(Player)

    team = tcrud.insert(name="red")
    pcrud.insert(name="alice", team_id=team.id)

    tcrud.delete_one(team)

    player = pcrud.get_or_none(name="alice")
    assert player is not None
    assert player.team_id is None

    engine.close()
    db_fk.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Type round-trips
# ---------------------------------------------------------------------------

def test_type_roundtrip():
    """bool, float, bytes, date, and time values survive a write/read cycle."""
    class TypeModel(Model):
        id: int = Field(pk=True, auto=True)
        flag: bool
        score: float
        blob: bytes
        born: date
        alarm: time

    db_types = path / "test_types.sqlite"
    db_types.unlink(missing_ok=True)
    try:
        with Engine(db_types) as engine:
            crud = engine.crud(TypeModel)
            obj = crud.insert(
                flag=True,
                score=3.14,
                blob=b"\x00\xff",
                born=date(1990, 5, 20),
                alarm=time(8, 0, 0),
            )
            assert obj.flag is True
            assert obj.score == pytest.approx(3.14)
            assert obj.blob == b"\x00\xff"
            assert obj.born == date(1990, 5, 20)
            assert obj.alarm == time(8, 0, 0)

            fetched = crud.get_or_none(id=obj.id)
            assert fetched.flag is True
            assert fetched.score == pytest.approx(3.14)
            assert fetched.blob == b"\x00\xff"
            assert fetched.born == date(1990, 5, 20)
            assert fetched.alarm == time(8, 0, 0)
    finally:
        db_types.unlink(missing_ok=True)
