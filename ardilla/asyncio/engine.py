from __future__ import annotations
import aiosqlite

from .crud import AsyncCrud
from ..models import M
from ..engine import Engine


class AsyncEngine(Engine):
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
            await con.commit()

    def crud(self, Model: type[M]) -> AsyncCrud[M]:
        return AsyncCrud(Model, self)
