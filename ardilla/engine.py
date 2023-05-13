from __future__ import annotations
import sqlite3

from .models import M
from .crud import Crud
from .abc import AbstractEngine

class ContextCursor:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def __enter__(self) -> sqlite3.Cursor:
        self.cur = self.con.cursor()
        return self.cur

    def __exit__(self, *_) -> None:
        self.cur.close()


class Engine(AbstractEngine):
    def __init__(self, path: str):
        self.path = path
        self.schemas: set[str] = set()
        self._cruds = {}

    def __enter__(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        self.con = con
        return con

    def __exit__(self, *_):
        self.con.close()

    def cursor(self, con: sqlite3.Connection) -> ContextCursor:
        return ContextCursor(con)

    def setup(self):
        with self as con:
            con.execute("PRAGMA foreign_keys = ON;")
            for table in self.schemas:
                con.execute(table)
            con.commit()
    
    def crud(self, Model: type[M]) -> Crud[M]:
        crud = self._cruds.setdefault(Model, Crud(Model, self))
        return crud
