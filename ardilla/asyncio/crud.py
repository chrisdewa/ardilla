from typing import Literal, Generic, Self

import aiosqlite
from aiosqlite import Row

from ..errors import QueryExecutionError
from ..models import M
from ..abc import CrudABC
from ..logging import log
from .. import queries

from .abc import AbstractAsyncEngine


class AsyncCrud(CrudABC, Generic[M]):
    """Abstracts CRUD actions for model associated tables"""

    engine: AbstractAsyncEngine

    async def get_or_none(self, **kws) -> M | None:
        """Gets an object from a database or None if not found"""
        q, vals = queries.for_get_or_none(self.tablename, kws)
        async with self.engine as con:
            async with con.execute(q, vals) as cur:
                row: Row | None = await cur.fetchone()
                if row:
                    return self._row2obj(row)
        return None

    async def _do_insert(self, ignore: bool = False, returning: bool = True, /, **kws):
        q, vals = queries.for_do_insert(self.tablename, ignore, returning, kws)

        async with self.engine as con:
            con = await self.engine.connect()
            cur = None
            try:
                cur = await con.execute(q, vals)
            except aiosqlite.IntegrityError as e:
                raise QueryExecutionError(str(e))
            else:
                row = await cur.fetchone()
                await con.commit()
                if returning and row:
                    return self._row2obj(row, cur.lastrowid)
            finally:
                if cur is not None:
                    await cur.close()
                await con.close()

    async def insert(self, **kws):
        """
        Inserts a record into the database.
        Returns:
            Model | None: Returns a model only if newly created
        Rises:
            ardilla.error.QueryExecutionError: if there's a conflict when inserting the record
        """
        return await self._do_insert(False, True, **kws)

    async def insert_or_ignore(self, **kws) -> M | None:
        """inserts a the object of a row or ignores it if it already exists"""
        return await self._do_insert(True, True, **kws)

    async def get_or_create(self, **kws) -> tuple[M, bool]:
        """Returns object and bool indicated if it was created or not"""
        created = False
        result = await self.get_or_none(**kws)
        if not result:
            result = await self.insert_or_ignore(**kws)
            created = True
        return result, created

    async def get_all(self) -> list[M]:
        """Gets all objects from the database"""
        q = f"SELECT rowid, * FROM {self.tablename};"
        log.debug(f"Querying: {q}")

        async with self.engine as con:
            async with con.execute(q) as cur:
                return [self._row2obj(row) for row in await cur.fetchall()]

    async def get_many(
        self,
        order_by: dict[str, str] | None = None,
        limit: int | None = None,
        **kws,
    ) -> list[M]:
        """Returns a list of objects that have the given conditions"""
        q, vals = queries.for_get_many(self.Model, order_by=order_by, limit=limit, kws=kws)
        async with self.engine as con:
            async with con.execute(q, vals) as cur:
                rows: list[Row] = await cur.fetchall()
                return [self._row2obj(row) for row in rows]

    async def save_one(self, obj: M) -> Literal[True]:
        """Saves one object to the database"""
        q, vals = queries.for_save_one(obj)

        async with self.engine as con:
            await con.execute(q, vals)
            await con.commit()
        return True

    async def save_many(self, *objs: M) -> Literal[True]:
        """Saves all the given objects to the database"""
        q, vals = queries.for_save_many(objs)

        async with self.engine as con:
            await con.executemany(q, vals)
            await con.commit()

        return True

    async def delete_one(self, obj: M) -> Literal[True]:
        """
        Deletes the object from the database (won't delete the actual object)
        queries only by the Model id fields (fields suffixed with 'id')
        """
        q, vals = queries.for_delete_one(obj)

        async with self.engine as con:
            await con.execute(q, vals)
            await con.commit()
        return True

    async def delete_many(self, *objs: M) -> Literal[True]:
        q, vals = queries.for_delete_many(objs)

        async with self.engine as con:
            await con.execute(q, vals)
            await con.commit()

        