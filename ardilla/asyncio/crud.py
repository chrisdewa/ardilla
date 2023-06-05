from __future__ import annotations
from typing import Literal, Generic, Optional, Union

from typing import Any
import aiosqlite
from aiosqlite import Row

from ..errors import BadQueryError, QueryExecutionError, disconnected_engine_error
from ..models import M
from ..abc import BaseCrud
from ..schemas import SQLFieldType
from ..errors import DisconnectedEngine
from .. import queries


class ConnectionProxy:
    """A proxy class for aiosqlite.Connection that
    checks if the connections is alive before returning any of its attributes
    
    Args:
        connection (aiosqlite.Connection)
    """
    def __init__(self, connection: aiosqlite.Connection):
        self._connection = connection
    
    def __getattr__(self, __name: str) -> Any:
        if __name in {'execute', 'commit'}:
            if not self._connection._running or not self._connection._connection:
                raise DisconnectedEngine('The engine is disconnected')
        return getattr(self._connection, __name)


class AsyncCrud(BaseCrud, Generic[M]):
    """Abstracts CRUD actions for model associated tables"""
    connection: aiosqlite.Connection
    
    def __init__(self, Model: type[M], connection: aiosqlite.Connection) -> None:
        connection = ConnectionProxy(connection)
        super().__init__(Model, connection)


    async def _do_insert(
        self,
        ignore: bool = False,
        returning: bool = True,
        /,
        **kws: SQLFieldType,
    ):
        """private helper method for insertion methods

        Args:
            ignore (bool, optional): Ignores conflicts silently. Defaults to False.
            returning (bool, optional): Determines if the query should return the inserted row. Defaults to True.
            kws (SQLFieldType): the column names and values for the insertion query

        Raises:
            QueryExecutionError: when sqlite3.IntegrityError happens because of a conflic

        Returns:
            An instance of model if any row is returned
        """
        q, vals = queries.for_do_insert(self.tablename, ignore, returning, kws)

        cur = None
        try:
            cur = await self.connection.execute(q, vals)
        except aiosqlite.IntegrityError as e:
            raise QueryExecutionError(str(e))
        except aiosqlite.ProgrammingError as e:
            raise disconnected_engine_error
        else:
            row = await cur.fetchone()
            await self.connection.commit()
            if returning and row:
                return self._row2obj(row, cur.lastrowid)
        finally:
            if cur is not None:
                await cur.close()

    async def get_or_none(self, **kws: SQLFieldType) -> Optional[M]:
        """Returns a row as an instance of the model if one is found or none

        Args:
            kws (SQLFieldType): The keyword arguments are passed as column names and values to
                a select query

        Example:
            ```py
            await crud.get_or_none(id=42)

            # returns an object with id of 42 or None if there isn't one in the database
            ```
        Returns:
            The object found with the criteria if any
        """
        self.verify_kws(kws)
        q, vals = queries.for_get_or_none(self.tablename, kws)

        async with self.connection.execute(q, vals) as cur:
            row: Union[Row, None] = await cur.fetchone()
            if row:
                return self._row2obj(row)
        return None

    async def insert(self, **kws: SQLFieldType) -> M:
        """
        Inserts a record into the database.

        Args:
            kws (SQLFieldType): the column names and values for the insertion query

        Returns:
            Returns the inserted row as an instance of the model
        Rises:
            ardilla.error.QueryExecutionError: if there's a conflict when inserting the record
        """
        self.verify_kws(kws)
        return await self._do_insert(False, True, **kws)

    async def insert_or_ignore(self, **kws: SQLFieldType) -> Optional[M]:
        """Inserts a record to the database with the keywords passed. It ignores conflicts.

        Args:
            kws (SQLFieldType): The keyword arguments are passed as the column names and values
                to the insert query

        Returns:
            The newly created row as an instance of the model if there was no conflicts
        """
        self.verify_kws(kws)
        return await self._do_insert(True, True, **kws)

    async def get_or_create(self, **kws: SQLFieldType) -> tuple[M, bool]:
        """Returns an object from the database with the spefied matching data
        Args:
            kws (SQLFieldType): the key value pairs will be used to query for an existing row
                if no record is found then a new row will be inserted
        Returns:
            A tuple with two values, the object and a boolean indicating if the
                object was newly created or not
        """
        created = False
        result = await self.get_or_none(**kws)
        if not result:
            result = await self.insert_or_ignore(**kws)
            created = True
        return result, created

    async def get_all(self) -> list[M]:
        """Gets all objects from the database

        Returns:
            A list with all the rows in table as instances of the model
        """
        q = f"SELECT rowid, * FROM {self.tablename};"

        async with self.connection.execute(q) as cur:
            return [self._row2obj(row) for row in await cur.fetchall()]

    async def get_many(
        self,
        order_by: Optional[dict[str, str]] = None,
        limit: Optional[int] = None,
        **kws: SQLFieldType,
    ) -> list[M]:
        """Queries the database and returns objects that meet the criteris

        Args:
            order_by (Optional[dict[str, str]], optional): An ordering dict. Defaults to None.
                The ordering should have the structure: `{'column_name': 'ASC' OR 'DESC'}`
                Case in values is insensitive
            kws (SQLFieldType): the column names and values for the select query

            limit (Optional[int], optional): The number of items to return. Defaults to None.

        Returns:
            a list of rows matching the criteria as intences of the model
        """
        self.verify_kws(kws)

        q, vals = queries.for_get_many(
            self.Model, order_by=order_by, limit=limit, kws=kws
        )
        async with self.connection.execute(q, vals) as cur:
            rows: list[Row] = await cur.fetchall()
            return [self._row2obj(row) for row in rows]

    async def save_one(self, obj: M) -> Literal[True]:
        """Saves one object to the database

        Args:
            obj (M): the object to persist

        Returns:
            The literal `True` if the method ran successfuly
        """
        q, vals = queries.for_save_one(obj)

        await self.connection.execute(q, vals)
        await self.connection.commit()
        return True

    async def save_many(self, *objs: M) -> Literal[True]:
        """Saves all the passed objects to the database

        Args:
            objs (M): the objects to persist

        Returns:
            The literal `True` if the method ran successfuly
        """
        q, vals = queries.for_save_many(objs)

        await self.connection.executemany(q, vals)
        await self.connection.commit()

        return True

    async def delete_one(self, obj: M) -> Literal[True]:
        """
        Deletes the object from the database (won't delete the actual object)
        If the object has a PK field or the rowid setup, those will be
        used to locate the obj and delete it.
        If not, this function will delete any row that meets the values of the object


        Args:
            obj (M): the object to delete

        Returns:
            The literal `True` if the method ran successfuly

        """
        q, vals = queries.for_delete_one(obj)

        await self.connection.execute(q, vals)
        await self.connection.commit()
        return True

    async def delete_many(self, *objs: M) -> Literal[True]:
        """
        Deletes all the objects passed

        Args:
            objs (M): the object to delete

        Returns:
            The literal `True` if the method ran successfuly

        """
        q, vals = queries.for_delete_many(objs)

        await self.connection.execute(q, vals)
        await self.connection.commit()
        
    async def count(self, column: str = '*', /, **kws) -> int:
        """Returns an integer of the number of non null values in a column
        Or the total number of rows if '*' is passed

        Args:
            column (str, optional): The column name to count rows on. 
                Defaults to '*' which counts all the rows in the table

        Returns:
            int: the number of rows with non null values in a column or the number of rows in a table
        """
        tablename = self.Model.__tablename__
        if column not in self.Model.__fields__ and column != '*':
            raise BadQueryError(f'"{column}" is not a field of the "{tablename}" table')
        
        q, vals = queries.for_count(tablename, column, kws)
        async with self.connection.execute(q, vals) as cur:
            row = await cur.fetchone()    
            count = row['total_count']
                
        return count