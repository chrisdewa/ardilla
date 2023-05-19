from __future__ import annotations
from typing import Coroutine
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
        self.acon = await self.connect()
        if self.enable_foreing_keys:
            await self.acon.execute('PRAGMA foreign_keys = on;')
        return self.acon

    async def __aexit__(self, *_):
        await self.acon.close()

    async def setup(self):
        async with self as con:
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