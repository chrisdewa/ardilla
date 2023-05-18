import sqlite3
from typing import Self, Literal, TypeVar, ContextManager, Protocol
from abc import abstractmethod, ABC
from sqlite3 import Row

from .errors import MissingEngine
from .models import M, Model as BaseModel

E = TypeVar("E")  # Engine Type


class ContextCursorProtocol(Protocol):
    def __init__(self, con: sqlite3.Connection):
        ...

    def __enter__(self) -> sqlite3.Cursor:
        ...

    def __exit__(self, *_) -> None:
        ...


class AbstractEngine(ABC):
    """This just provides autocompletition across the library"""

    schemas: set[str]

    @abstractmethod
    def __enter__(self) -> sqlite3.Connection:
        ...

    @abstractmethod
    def __exit__(self, *_) -> None:
        ...

    @abstractmethod
    def cursor(self, con: sqlite3.Connection) -> ContextCursorProtocol:
        ...


class CrudABC(ABC):
    __slots__ = (
        "engine",
        "tablename",
        "Model",
        "columns",
    )

    engine: AbstractEngine

    def __init__(self, Model: type[M], engine: AbstractEngine | None = None) -> None:
        if engine:
            self.engine = engine

        self.Model = Model
        if Model.__schema__:
            self.engine.schemas.add(Model.__schema__)
        self.tablename = Model.__tablename__
        self.columns = tuple(Model.__fields__)

    def __new__(cls, Model: type[M], engine: AbstractEngine | None = None) -> Self:
        if not issubclass(Model, BaseModel):
            raise TypeError("Model param has to be a subclass of model")

        cls_engine = getattr(cls, "engine", None)

        if engine is None and cls_engine is None:
            # if not isinstance(engine, Engine) and not isinstance(cls_engine, Engine):
            raise MissingEngine(
                "Missing engine. Set the engine at instance level (Crud(Model, engine))"
                "or at class level (Crud.engine = engine)"
            )
        return super().__new__(cls)

    def _row2obj(self, row: Row, rowid: int | None = None) -> BaseModel:
        """
        Args:
            row: the sqlite row
            rowid: the rowid of the row.
                If passed it means it comes from an insert function

        """
        [*keys] = self.Model.__fields__
        if rowid is None:
            rowid, *vals = row
        else:
            vals = list(row)
        data = {k: v for k, v in zip(keys, vals)}

        obj = self.Model(**data)
        obj.__rowid__ = rowid
        return obj

    # Create
    @abstractmethod
    def _do_insert(self, ignore: bool = False, returning: bool = True, /, **kws):
        pass

    @abstractmethod
    def insert(self, **kws):
        pass

    @abstractmethod
    def insert_or_ignore(self):
        pass

    # Read
    @abstractmethod
    def get_all(self) -> list[M]:
        pass

    @abstractmethod
    def get_many(self, **kws) -> list[M]:
        pass

    @abstractmethod
    def get_or_create(self, **kws) -> tuple[M, bool]:
        pass

    @abstractmethod
    def get_or_none(self, **kws) -> M | None:
        pass

    @abstractmethod
    def _get_or_none_any(self, many: bool, **kws) -> list[BaseModel] | BaseModel | None:
        pass

    # Update
    @abstractmethod
    def save_one(self, obj: M) -> Literal[True]:
        pass

    @abstractmethod
    def save_many(self, *objs: M) -> Literal[True]:
        pass

    # Delete
    @abstractmethod
    def delete_one(self, obj: M) -> Literal[True]:
        pass

    @abstractmethod
    def delete_many(self, *objs: M) -> Literal[True]:
        pass
