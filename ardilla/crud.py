from __future__ import annotations
import sqlite3
from sqlite3 import Row
from contextlib import contextmanager
from typing import Literal, Generic, Optional, Union, Generator

from . import queries
from .abc import BaseCrud
from .models import M
from .errors import BadQueryError, QueryExecutionError, disconnected_engine_error, DisconnectedEngine
from .schemas import SQLFieldType


@contextmanager
def contextcursor(con: sqlite3.Connection) -> Generator[sqlite3.Cursor, None, None]:
    """a context manager wrapper for sqlite3.Cursor

    Args:
        con (sqlite3.Connection): the connection

    Raises:
        disconnected_engine_error: if the connection is non functioning

    Yields:
        Generator[sqlite3.Cursor, None, None]: the cursor
    """
    cur = None
    try:
        cur = con.cursor()
        yield cur
    except Exception as e:
        if (
            isinstance(e, sqlite3.ProgrammingError)
            and str(e) == "Cannot operate on a closed database."
        ):
            raise DisconnectedEngine(str(e))
        else:
            raise e
    finally:
        if cur is not None:
            cur.close()


class Crud(BaseCrud, Generic[M]):
    """Abstracts CRUD actions for model associated tables"""

    connection: sqlite3.Connection

    def _do_insert(
        self,
        ignore: bool = False,
        returning: bool = True,
        /,
        **kws: SQLFieldType,
    ) -> Optional[M]:
        """private helper method for insertion methods

        Args:
            ignore (bool, optional): Ignores conflicts silently. Defaults to False.
            returning (bool, optional): Determines if the query should return the inserted row. Defaults to True.
            kws (SQLFieldType): the column name and values for the insert query

        Raises:
            QueryExecutionError: when sqlite3.IntegrityError happens because of a conflic

        Returns:
            An instance of model if any row is returned
        """
        q, vals = queries.for_do_insert(self.tablename, ignore, returning, kws)

        with contextcursor(self.connection) as cur:
            try:
                cur.execute(q, vals)
            except sqlite3.IntegrityError as e:
                raise QueryExecutionError(str(e))

            row = cur.fetchone()
            self.connection.commit()
            if returning and row:
                return self._row2obj(row, cur.lastrowid)

        return None

    def insert(self, **kws: SQLFieldType) -> M:
        """Inserts a record into the database.

        Args:
            kws (SQLFieldType): The keyword arguments are passed as the column names and values
                to the insert query

        Returns:
            Creates a new entry in the database and returns the object

        Rises:
            `ardilla.error.QueryExecutionError`: if there's a conflict when inserting the record
        """
        self.verify_kws(kws)
        return self._do_insert(False, True, **kws)

    def insert_or_ignore(self, **kws: SQLFieldType) -> Optional[M]:
        """Inserts a record to the database with the keywords passed. It ignores conflicts.

        Args:
            kws (SQLFieldType): The keyword arguments are passed as the column names and values
                to the insert query

        Returns:
            The newly created row as an instance of the model if there was no conflicts
        """
        self.verify_kws(kws)
        return self._do_insert(True, True, **kws)
    
    def get_or_none(self, **kws: SQLFieldType) -> Optional[M]:
        """Returns a row as an instance of the model if one is found or none

        Args:
            kws (SQLFieldType): The keyword arguments are passed as column names and values to
                a select query

        Example:
            ```py
            crud.get_or_none(id=42)

            # returns an object with id of 42 or None if there isn't one in the database
            ```

        Returns:
            The object found with the criteria if any
        """
        self.verify_kws(kws)
        q, vals = queries.for_get_or_none(self.tablename, kws)
        with contextcursor(self.connection) as cur:
            cur.execute(q, vals)
            row: Union[Row, None] = cur.fetchone()
            if row:
                return self._row2obj(row)
        return None

    def get_or_create(self, **kws: SQLFieldType) -> tuple[M, bool]:
        """Returns an object from the database with the spefied matching data
        Args:
            kws (SQLFieldType): the key value pairs will be used to query for an existing row
                if no record is found then a new row will be inserted
        Returns:
            A tuple with two values, the object and a boolean indicating if the
                object was newly created or not
        """
        self.verify_kws(kws)
        created = False
        result = self.get_or_none(**kws)
        if not result:
            result = self.insert_or_ignore(**kws)
            created = True
        return result, created

    def get_all(self) -> list[M]:
        """Gets all objects from the database
        Returns:
            A list with all the rows in table as instances of the model
        """
        return self.get_many()

    def get_many(
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

            limit (Optional[int], optional): The number of items to return. Defaults to None.
            kws (SQLFieldType): The column names and values for the select query

        Returns:
            a list of rows matching the criteria as intences of the model
        """
        self.verify_kws(kws)
        q, vals = queries.for_get_many(
            self.Model, 
            order_by=order_by,
            limit=limit, 
            kws=kws,
        )
        with contextcursor(self.connection) as cur:
            cur.execute(q, vals)
            rows: list[Row] = cur.fetchall()
            return [self._row2obj(row) for row in rows]

    def save_one(self, obj: M) -> Literal[True]:
        """Saves one object to the database

        Args:
            obj (M): the object to persist

        Returns:
            The literal `True` if the method ran successfuly
        """
        q, vals = queries.for_save_one(obj)
        try:
            self.connection.execute(q, vals)
            self.connection.commit()
        except:
            raise disconnected_engine_error
        return True

    def save_many(self, *objs: tuple[M]) -> Literal[True]:
        """Saves all the passed objects to the database

        Args:
            objs (M): the objects to persist

        Returns:
            The literal `True` if the method ran successfuly
        """
        q, vals = queries.for_save_many(objs)
        try:
            self.connection.executemany(q, vals)
            self.connection.commit()
        except:
            raise disconnected_engine_error

        return True

    def delete_one(self, obj: M) -> Literal[True]:
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
        try:
            self.connection.execute(q, vals)
            self.connection.commit()
        except:
            raise disconnected_engine_error
        return True

    def delete_many(self, *objs: M) -> Literal[True]:
        """
        Deletes all the objects passed

        Args:
            objs (M): the object to delete

        Returns:
            The literal `True` if the method ran successfuly

        """
        q, vals = queries.for_delete_many(objs)
        try:
            self.connection.execute(q, vals)
            self.connection.commit()
        except:
            raise disconnected_engine_error
        return True

    def count(self, column: str = '*',/, **kws) -> int:
        """Returns an integer of the number of non null values in a column
        Or the total number of rows if '*' is passed

        Args:
            column (str, optional): The column name to count rows on. 
                Defaults to '*' which counts all the rows in the table

        Returns:
            int: the number of rows with non null values in a column or the number of rows in a table
        """
        self.verify_kws(kws)
        
        tablename = self.Model.__tablename__
        if column not in self.Model.__fields__ and column != '*':
            raise BadQueryError(f'"{column}" is not a field of the "{tablename}" table')
        
        
        q, vals = queries.for_count(tablename, column, kws)
        with contextcursor(self.connection) as cur:
            cur.execute(q, vals)
            row = cur.fetchone()
    
            count = row['total_count']
                
        return count