from __future__ import annotations

import aiosqlite

from ..abc import BaseEngine
from ..models import M
from ..errors import DisconnectedEngine

from .crud import AsyncCrud

class AsyncEngine(BaseEngine):
    """Async Engine that uses `aiosqlite.Connection` and `aiosqlite.Cursor`
    """
    con: aiosqlite.Connection
    
    async def connect(self) -> aiosqlite.Connection:
        """
        Stablishes a connection to the database
        Returns:
            The connection
        """
        await self.close()
        con = await aiosqlite.connect(self.path)
        con.row_factory = aiosqlite.Row
        if self.enable_foreing_keys:
            await con.execute('PRAGMA foreign_keys = ON;')
        self.con = con
        return con

    async def close(self) -> None:
        if self.check_connection():
            await self.con.close()

    async def __aenter__(self) -> AsyncEngine:
        """Stablishes the connection and if specified enables foreign keys pragma

        Returns:
            The connection
        """
        await self.connect()
        return self

    async def __aexit__(self, *_):
        """Closes the connection"""
        await self.close()
    
    async def crud(self, Model: type[M]) -> AsyncCrud[M]:
        """
        This function works exactly like `Engine.crud` but
        returns an instance of `ardilla.asyncio.crud.AsyncCrud` instead of `ardilla.crud.Crud`
        and is asynchronous
        
        Returns:
            The async Crud for the given model
        """
        if not self.check_connection():
            raise DisconnectedEngine("Can't create crud objects with a disconnected engine")
            
        if Model.__schema__ not in self.tables_created:
            await self.con.execute(Model.__schema__)
            await self.con.commit()
            self.tables_created.add(Model.__schema__)
            
        return AsyncCrud(Model, self.con)
