from __future__ import annotations
import aiosqlite

from .crud import AsyncCrud
from ..models import M
from ..engine import Engine

from .abc import AbstractAsyncEngine


class AsyncEngine(Engine, AbstractAsyncEngine):
    async def connect(self) -> aiosqlite.Connection:
        con = await aiosqlite.connect(self.path)
        con.row_factory = aiosqlite.Row
        return con

    async def __aenter__(self) -> aiosqlite.Connection:
        self.con = await self.connect()
        return self.con

    async def __aexit__(self, *_):
        await self.con.close()

    async def setup(self):
        async with self as con:
            await con.execute("PRAGMA foreign_keys = ON;")
            for table in self.schemas:
                await con.execute(table)
                self.tables_created.add(table)
            await con.commit()
    
    def crud(self, Model: type[M]) -> AsyncCrud[M]:
        """This function runs synchronously"""
        crud = self._cruds.setdefault(Model, AsyncCrud(Model, self))
        if Model.__schema__ not in self.tables_created:
            with self as con:
                con.execute(Model.__schema__)
                con.commit()
            self.tables_created.add(Model.__schema__)
        return crud