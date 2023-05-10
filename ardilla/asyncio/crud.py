from typing import Literal, Generic, Self

import aiosqlite

from .engine import AsyncEngine

from ..errors import QueryExecutionError
from ..models import M
from ..abc import CrudABC


class AsyncCrud(CrudABC, Generic[M]):
    """Abstracts CRUD actions for model associated tables"""
    engine: AsyncEngine
    
    async def _get_or_none_any(self, many: bool, **kws):
        """
        private helper to the get_or_none queries.
        if param "many" is true it will return a list of matches else will return only one record
        """
        keys, vals = zip(*kws.items())
        to_match = f" AND ".join(f"{k} = ?" for k in keys)

        limit = 'LIMIT 1;' if not many else ';'
        q = f"SELECT * FROM {self.tablename} WHERE ({to_match}) {limit}"

        async with self.engine as con:
            async with con.execute(q, vals) as cur:
                if many:
                    result = await cur.fetchall()
                    return [self.Model(**entry) for entry in result]

                else:
                    result = await cur.fetchone()
                    if result:
                        return self.Model(**result)

    async def get_or_none(self, **kws) -> M | None:
        """Gets an object from a database or None if not found"""
        return await self._get_or_none_any(many=False, **kws)

    async def _do_insert(self, ignore: bool = False, returning: bool = True, / , **kws):
        keys, vals = zip(*kws.items())
        placeholders = ", ".join("?" * len(keys))
        cols = ", ".join(keys)
        
        q = "INSERT OR IGNORE " if ignore else "INSERT "
        q += f"INTO {self.tablename} ({cols}) VALUES ({placeholders})"
        q += " RETURNING *;" if returning else ";"
        
        async with self.engine as con:
            con = await self.engine.connect()
            cur = None
            try:
                cur = await con.execute(q, vals)
            except aiosqlite.IntegrityError as e:
                raise QueryExecutionError(str(e))
            else:
                result = await cur.fetchone()
                await con.commit()
                if returning and result:
                    item =  self.Model(**result)
                    item.__rowid__ = cur.lastrowid
                    return item
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
        async with self.engine as con:
            async with con.execute(f"SELECT * FROM {self.tablename};") as cur:
                return [self.Model(**row) for row in await cur.fetchall()]

    async def get_many(self, **kws) -> list[M]:
        """Returns a list of objects that have the given conditions"""
        return await self._get_or_none_any(many=True, **kws)

    async def save_one(self, obj: M) -> Literal[True]:
        """Saves one object to the database"""
        cols, vals = zip(*obj.dict().items())
        placeholders = ", ".join("?" * len(cols))

        upsert_query = f"""
        INSERT OR REPLACE INTO {self.tablename} ({', '.join(cols)}) VALUES ({placeholders});
        """

        async with self.engine as con:
            await con.execute(upsert_query, vals)
            await con.commit()
        return True

    async def save_many(self, *objs: M) -> Literal[True]:
        """Saves all the given objects to the database"""
        placeholders = ", ".join("?" * len(self.columns))
        q = f'INSERT OR REPLACE INTO {self.tablename} ({", ".join(self.columns)}) VALUES ({placeholders});'
        vals = [tuple(obj.dict().values()) for obj in objs]
        async with self.engine as con:
            await con.executemany(q, vals)
            await con.commit()

        return True

    async def delete_one(self, obj: M) -> Literal[True]:
        """
        Deletes the object from the database (won't delete the actual object)
        queries only by the Model id fields (fields suffixed with 'id')
        """
        obj_dict = obj.dict()
        id_cols = tuple([k for k in obj_dict if "id" in k])
        placeholders = ", ".join(f"{k} = ?" for k in id_cols)
        vals = tuple([obj_dict[k] for k in id_cols])
        q = f"DELETE FROM {self.tablename} WHERE ({placeholders});"
        async with self.engine as con:
            await con.execute(q, vals)
            await con.commit()
        return True

    async def delete_many(self, *objs: M) -> Literal[True]:
        if not objs:
            raise IndexError('param "objs" is empty, pass at least one object')

        prot = objs[0]
        id_cols = tuple([k for k in prot.dict() if "id" in k])
        placeholders = " OR ".join(
            f"({', '.join(f'{k} = ?' for k in id_cols)})" for _ in objs
        )
        vals = tuple(
            [val for obj in objs for key, val in obj.dict().items() if key in id_cols]
        )

        q = f"DELETE FROM {self.tablename} WHERE {placeholders};"
        async with self.engine as con:
            await con.execute(q, vals)
            await con.commit()

        return True
