from __future__ import annotations
import aiosqlite

from .crud import AsyncCrud
from ..models import M
from ..engine import Engine

from .abc import AbstractAsyncEngine

class AsyncEngine(Engine, AbstractAsyncEngine):
    """Async Engine that uses `aiosqlite.Connection` and `aiosqlite.Cursor`
    Inhetits attributes from `Engine`
    """
    def __init__(self, path: str, enable_foreing_keys: bool = False, single_connection: bool = False):
        if single_connection is True:
            raise NotImplementedError('The async engine does not support single connection for now')
        super().__init__(path, enable_foreing_keys, single_connection)
    
    async def connect(self) -> aiosqlite.Connection:
        """
        Stablishes a connection to the database
        Returns:
            The connection
        """
        con = await aiosqlite.connect(self.path)
        con.row_factory = aiosqlite.Row
        return con

    async def __aenter__(self) -> aiosqlite.Connection:
        """Stablishes the connection and if specified enables foreign keys pragma

        Returns:
            The connection
        """
        self.acon = await self.connect()
        if self.enable_foreing_keys:
            await self.acon.execute('PRAGMA foreign_keys = ON;')
            
        return self.acon

    async def __aexit__(self, *_):
        """Closes the connection"""
        await self.acon.close()

    async def setup(self):
        """Creates the tables setup by the engine
        """
        async with self as con:
            for table in self.schemas:
                await con.execute(table)
                self.tables_created.add(table)
            await con.commit()
    
    def crud(self, Model: type[M]) -> AsyncCrud[M]:
        """
        This function runs synchronously and works exactly like `Engine.crud` but
        returns an instance of `ardilla.asyncio.crud.AsyncCrud` instead of `ardilla.crud.Crud`
        
        Returns:
            The async Crud for the given model
        """
        crud = self._cruds.setdefault(Model, AsyncCrud(Model, self))
        if Model.__schema__ not in self.tables_created:
            with self as con:
                con.execute(Model.__schema__)
                con.commit()
            self.tables_created.add(Model.__schema__)
        return crud