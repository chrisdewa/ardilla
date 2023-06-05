from __future__ import annotations
import sqlite3
from typing import Any, Literal, TypeVar, Optional, Union
from abc import abstractmethod, ABC
from sqlite3 import Row

from .models import M, Model as BaseModel

E = TypeVar("E")  # Engine Type

Connection = TypeVar("Connection")
CrudType = TypeVar('CrudType', bound='BaseCrud')


class BaseEngine(ABC):
    """This just provides autocompletition across the library"""

    __slots__ = (
        "path",  # the path to the database
        "schemas",  # the registered tables
        "tables_created",  # a list of tables that were setup
        "enable_foreing_keys",  # a bool to specify if the pragma should be enforced
        "con", # sync connection
        "_cruds", # crud cache
    )
    
    def check_connection(self) -> bool:
        """Checks if the engine's connection is alive
        works for both the sync and async classes

        Returns:
            bool: if the connection is fine
        """
        con: Union[Connection, None] = getattr(self, 'con', None)
        try:
            if isinstance(con, sqlite3.Connection):
                con.cursor()
                return True
            elif con is not None:
                # should be aiosqlite
                # we don't import it here to prevent import errors 
                # in case there's missing dependency of aiosqlite
                return con._running and con._connection
            else:
                return None
        except:
            return False

    def __init__(
        self,
        path: str,
        enable_foreing_keys: bool = False,
    ):
        self.path = path
        self.schemas: set[str] = set()
        self.tables_created: set[str] = set()
        self._cruds: dict[type[M], CrudType] = {}
        self.enable_foreing_keys = enable_foreing_keys
    
    @abstractmethod
    def get_connection(self) -> Connection:
        ...
        
    @abstractmethod
    def connect(self) -> Connection:
        ...
        
    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def crud(self, Model: type[M]) -> CrudType:
        ...


class BaseCrud(ABC):
    __slots__ = (
        "connection",
        "tablename",
        "Model",
        "columns",
    )

    def __init__(self, Model: type[M], connection: Connection) -> None:
        self.Model = Model
        self.connection = connection

        self.tablename = Model.__tablename__
        self.columns = tuple(Model.__fields__)

    def __new__(cls, Model: type[M], connection: Connection):
        if not issubclass(Model, BaseModel):
            raise TypeError("Model param has to be a subclass of model")

        return super().__new__(cls)

    def verify_kws(self, kws: dict[str, Any]) -> Literal[True]:
        """Verifies that the passed kws keys in dictionary
        are all contained within the model's fields

        Args:
            kws (dict[str, Any]): the keyword arguments for queries

        Returns:
            Literal[True]: If the kws are verified
        """
        for key in kws:
            if key not in self.Model.__fields__:
                raise KeyError(
                    f'"{key}" is not a field of the "{self.Model.__name__}" and cannot be used in queries'
                )
        return True

    def _row2obj(self, row: Row, rowid: Optional[int] = None) -> BaseModel:
        """
        Args:
            row: the sqlite row
            rowid: the rowid of the row.
                If passed it means it comes from an insert function

        """
        keys = list(self.Model.__fields__)
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
        ...

    @abstractmethod
    def insert(self, **kws):
        ...

    @abstractmethod
    def insert_or_ignore(self):
        ...

    # Read
    @abstractmethod
    def get_all(self) -> list[M]:
        ...

    @abstractmethod
    def get_many(
        self,
        order_by: Optional[dict[str, str]] = None,
        limit: Optional[int] = None,
        **kws,
    ) -> list[M]:
        ...

    @abstractmethod
    def get_or_create(self, **kws) -> tuple[M, bool]:
        ...

    @abstractmethod
    def get_or_none(self, **kws) -> Optional[M]:
        ...

    # Update
    @abstractmethod
    def save_one(self, obj: M) -> Literal[True]:
        ...

    @abstractmethod
    def save_many(self, *objs: M) -> Literal[True]:
        ...

    # Delete
    @abstractmethod
    def delete_one(self, obj: M) -> Literal[True]:
        ...

    @abstractmethod
    def delete_many(self, *objs: M) -> Literal[True]:
        ...

    @abstractmethod
    def count(self, column: str = '*', /, **kws) -> int:
        ...