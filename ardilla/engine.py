from __future__ import annotations
import sqlite3

from .models import M
from .crud import Crud
from .abc import AbstractEngine, ContextCursorProtocol
from .logging import log


class ContextCursor(ContextCursorProtocol):
    """Wrapper for sqlite3.Cursor to automatically close the cursor when exiting the context
    
    Args: 
        con (sqlite3.Connection): the connection to get the cursor from
    """
    __slots__ = ('con', 'cur')
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def __enter__(self) -> sqlite3.Cursor:
        """Entry point for the context manager
        
        Returns:
            sqlite3.Cursor
        """
        self.cur = self.con.cursor()
        return self.cur

    def __exit__(self, *_) -> None:
        """closes the cursor opened on entering the context"""
        self.cur.close()


class Engine(AbstractEngine):
    """The sync engine that uses `sqlite3.Connection` and `sqlite3.Cursor`
    
    Args:
        path (str): a pathlike object that points to the sqlite database
        enable_foreing_keys (bool, optional): specifies if the pragma should be enforced. Defaults to False.
        single_connection (bool, optional): specifies if the engine should maintain a single connectio. Defaults to False.
    
    Attributes:
        path (str): the path to the db
        schemas (set[str]): a set of table schemas
        _cruds (dict[type[M], Crud[M]]): the cache for crud objects
        tables_created (set[str]): the tables that have been setup by the engine
        enable_foreing_keys (bool): if True, the engine enables the pragma on all connections
        single_connection (bool): if True, the engine maintains a single connection until closed
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
        """context manager entry point

        Returns:
            `sqlite3.Connection`
        """
        if not hasattr(self, 'con'):    
            con = sqlite3.connect(self.path)
            con.row_factory = sqlite3.Row
            self.con = con
            if self.enable_foreing_keys:
                self.con.execute("PRAGMA foreign_keys = on;")

        return self.con

    def __exit__(self, *_):
        """Connection context manager to close the connection
        Only actually closes it if `single_connection` is set to `True`
        """
        if not self.single_connection:
            self.con.close()
            delattr(self, 'con')
    
    def close(self):
        """Manually closes the connection if any
        """
        if hasattr(self, 'con'):
            self.con.close()
            delattr(self, 'con')
        
            

    def cursor(self, con: sqlite3.Connection) -> ContextCursor:
        """Fetches an ardilla.engine.ContextCursor 
        which wraps the sqlite3.Cursor with a context manager that 
        closes the cursor automatically
        
        Args:
            con (sqlite.Connection): the connectio to get the cursor from
        
        Returns:
            ContextCursor
        """
        return ContextCursor(con)

    def setup(self):
        """Manually sets up all the registered tables"""
        with self as con:
            for table in self.schemas:
                con.execute(table)
                self.tables_created.add(table)
            con.commit()

    def crud(self, Model: type[M]) -> Crud[M]:
        """returns a Crud instances for the given model type

        Args:
            Model (type[M]): the model type for the crud object

        Returns:
            Crud[M]: the crud for the model type
        """
        crud = self._cruds.setdefault(Model, Crud(Model, self))
        if Model.__schema__ not in self.tables_created:
            with self as con:
                con.execute(Model.__schema__)
                con.commit()
            self.tables_created.add(Model.__schema__)
        return crud
