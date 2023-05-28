from __future__ import annotations
import sqlite3

from .models import M
from .crud import Crud
from .abc import BaseEngine
from .errors import DisconnectedEngine

class Engine(BaseEngine):
    """The sync engine that uses `sqlite3.Connection` and `sqlite3.Cursor`
    
    Args:
        path (str): a pathlike object that points to the sqlite database
        enable_foreing_keys (bool, optional): specifies if the pragma should be enforced. Defaults to False.
    
    Attributes:
        path (str): the path to the db
        schemas (set[str]): a set of table schemas
        tables_created (set[str]): the tables that have been setup by the engine
        enable_foreing_keys (bool): if True, the engine enables the pragma on all connections
    """
    con: sqlite3.Connection
        
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, *_):
        self.close()
    
    def connect(self) -> sqlite3.Connection:
        self.close()
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        
        if self.enable_foreing_keys:
            con.execute("PRAGMA foreign_keys = on;")
        self.con = con
        return con

    def close(self) -> None:
        if self.check_connection():
            self.con.close()
        self._cruds.clear()
    
    def crud(self, Model: type[M]) -> Crud[M]:
        """returns a Crud instances for the given model type

        Args:
            Model (type[M]): the model type for the crud object

        Returns:
            Crud[M]: the crud for the model type
        """
        if not self.check_connection():
            raise DisconnectedEngine("Can't create crud objects with a disconnected engine")
        
        if Model.__schema__ not in self.tables_created:
            self.con.execute(Model.__schema__)
            self.con.commit()
            self.tables_created.add(Model.__schema__)
        
        crud = self._cruds.setdefault(Model, Crud(Model, self.con))
        
        return crud

