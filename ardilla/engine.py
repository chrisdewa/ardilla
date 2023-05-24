from __future__ import annotations
import sqlite3

from .models import M
from .crud import Crud
from .abc import AbstractEngine, ContextCursorProtocol
from .logging import log


class ContextCursor(ContextCursorProtocol):
    __slots__ = ('con', 'cur')
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def __enter__(self) -> sqlite3.Cursor:
        self.cur = self.con.cursor()
        return self.cur

    def __exit__(self, *_) -> None:
        self.cur.close()


class Engine(AbstractEngine):
    """Represents the sync engine that uses `sqlite3.connection`
    
    Args (init):
        path (str): a pathlike object that points to the sqlite database
        enable_foreing_keys (bool, optional): specifies if the pragma should be enforced. Defaults to False.
        single_connection (bool, optional): specifies if the engine should maintain a single connectio. Defaults to False.
    """
    
    __slots__ = ( 
        'path', # the path to the database
        'schemas', # the registered tables
        '_cruds', # the crud cache for the registered models
        'tables_created', # a list of tables that were setup
        'enable_foreing_keys', # a bool to specify if the pragma should be enforced
        'con', # the sync connection
        'single_connection', # if the engine should maintain a single connection
        'acon', # the async connection
    )
    def __init__(
        self,
        path: str,
        enable_foreing_keys: bool = False,
        single_connection: bool = False,
    ):
        self.path = path
        self.schemas: set[str] = set()
        self._cruds: dict[type[M], Crud[M]] = {}
        self.tables_created: set[str] = set()
        self.enable_foreing_keys = enable_foreing_keys
        self.single_connection = single_connection
        log.debug(f"Instantiating {self.__class__.__name__}")

    def __enter__(self) -> sqlite3.Connection:
        if not hasattr(self, 'con'):    
            con = sqlite3.connect(self.path)
            con.row_factory = sqlite3.Row
            self.con = con
            if self.enable_foreing_keys:
                self.con.execute("PRAGMA foreign_keys = on;")

        return self.con

    def __exit__(self, *_):
        if not self.single_connection:
            self.con.close()
            delattr(self, 'con')
    
    def close(self):
        if hasattr(self, 'con'):
            self.con.close()
            delattr(self, 'con')
        
            

    def cursor(self, con: sqlite3.Connection) -> ContextCursor:
        return ContextCursor(con)

    def setup(self):
        with self as con:
            for table in self.schemas:
                con.execute(table)
                self.tables_created.add(table)
            con.commit()

    def crud(self, Model: type[M]) -> Crud[M]:
        crud = self._cruds.setdefault(Model, Crud(Model, self))
        if Model.__schema__ not in self.tables_created:
            with self as con:
                con.execute(Model.__schema__)
                con.commit()
            self.tables_created.add(Model.__schema__)
        return crud
