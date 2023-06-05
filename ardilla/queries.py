"""
Methods here are used by Crud classes to obtain the query 
strings and variable tuples to pass to the connections and cursors
"""
from typing import Any, Optional, Union
from .errors import BadQueryError
from .models import M
from .ordering import validate_ordering
from .logging import log_query


def for_get_or_none(tablename: str, kws: dict) -> tuple[str, tuple[Any, ...]]:
    """called by _get_or_none_one method
    Args:
        tablename (str): name of the table
        kws (dict): the keywords to identify the rows with
    Returns:
        tuple[str, tuple[Any, ...]]: the query and values.
    """
    keys, vals = zip(*kws.items())
    to_match = f" AND ".join(f"{k} = ?" for k in keys)
    q = f"SELECT rowid, * FROM {tablename} WHERE ({to_match}) LIMIT 1;"
    log_query(q, vals)
    return q, vals


def for_get_many(
    Model: M,
    *,
    order_by: Optional[dict[str, str]] = None,
    limit: Optional[int] = None,
    kws: dict,
) -> tuple[str, tuple[Any, ...]]:
    """called by _get_many method
    Args:
     Args:
        Model (Model): the model of the table
        order_by (dict[str, str] | None ):
            if passed Defines the sorting methods for the query
            defaults to no sorting
        limit (int | None) an integer to determine the number of items to grab
        kws (dict): the keywords to identify the rows with
    """
    tablename = Model.__tablename__
    columns = tuple(Model.__fields__)

    if kws:
        keys, vals = zip(*kws.items())
        to_match = f" AND ".join(f"{k} = ?" for k in keys)
        filter_ = f" WHERE ({to_match})"
    else:
        filter_ = ""
        vals = ()

    if order_by is not None:
        ord = validate_ordering(columns, order_by)
        order_by_q = f" ORDER BY " + ", ".join(f"{k} {v}" for k, v in ord.items())
    else:
        order_by_q = ""

    if limit is not None:
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit, when passed, must be an integer larger than zero")
        limit_q = " LIMIT ?"
        vals += (limit,)
    else:
        limit_q = ""

    q = f"SELECT rowid, * FROM {tablename}{filter_}{order_by_q}{limit_q};"
    return q, vals


def for_do_insert(
    tablename: str,
    ignore: bool,
    returning: bool,
    kws: dict,
) -> tuple[str, tuple[Any, ...]]:
    """called by _do_insert methods

    Args:
        tablename (str): name of the table
        ignore (bool): whether or not to use `INSERT OR IGNORE` vs just `INSERT`
        returning (bool): if the inserted values should be returned by the query
        kws (dict): the keywords representing column name and values

    Returns:
        tuple[str, tuple[Any, ...]]: the queries and values
    """
    keys, vals = zip(*kws.items())
    placeholders = ", ".join("?" * len(keys))
    cols = ", ".join(keys)

    q = "INSERT OR IGNORE " if ignore else "INSERT "
    q += f"INTO {tablename} ({cols}) VALUES ({placeholders})"
    q += " RETURNING *;" if returning else ";"
    log_query(q, vals)
    return q, vals


def for_save_one(obj: M) -> tuple[str, tuple[Any, ...]]:
    """called by save_one methods

    Args:
        obj (M): the Model instance to save

    Returns:
        tuple[str, tuple[Any, ...]]: the query and values
    """
    cols, vals = zip(*obj.dict().items())

    if obj.__rowid__ is not None:
        q = f"""
        UPDATE {obj.__tablename__} SET {', '.join(f'{k} = ?' for k in cols)} WHERE rowid = ?;
        """
        vals += (obj.__rowid__,)

    else:
        placeholders = ", ".join("?" * len(cols))
        q = f"""
        INSERT OR REPLACE INTO {obj.__tablename__} ({', '.join(cols)}) VALUES ({placeholders});
        """
    log_query(q, vals)
    return q, vals


def for_save_many(objs: tuple[M]) -> tuple[str, tuple[Any, ...]]:
    """called by save_many methods

    Args:
        objs (tuple[M]): the objects to save

    Raises:
        BadQueryError: if the objs tuple is empty

    Returns:
        tuple[str, tuple[Any, ...]]: the query and values
    """
    if not objs:
        raise BadQueryError("To save many, you have to at least past one object")
    cols = tuple(objs[0].__fields__)
    tablename = objs[0].__tablename__
    placeholders = ", ".join("?" * len(cols))
    q = f'INSERT OR REPLACE INTO {tablename} ({", ".join(cols)}) VALUES ({placeholders});'
    vals = tuple(tuple(obj.dict().values()) for obj in objs)
    log_query(q, vals)
    return q, vals


def for_delete_one(obj: M) -> tuple[str, tuple[Any, ...]]:
    """called by delete_one methods

    Args:
        obj (M): the object to delete

    Returns:
        tuple[str, tuple[Any, ...]]: the query and values
    """
    tablename = obj.__tablename__
    if obj.__pk__:
        q = f"DELETE FROM {tablename} WHERE {obj.__pk__} = ?"
        vals = (getattr(obj, obj.__pk__),)
    elif obj.__rowid__:
        q = f"DELETE FROM {tablename} WHERE rowid = ?"
        vals = (obj.__rowid__,)
    else:
        obj_dict = obj.dict()
        placeholders = " AND ".join(f"{k} = ?" for k in obj_dict)
        vals = tuple(obj_dict[k] for k in obj_dict)
        q = f"""
        DELETE FROM {tablename} WHERE ({placeholders});
        """
    log_query(q, vals)
    return q, vals


def for_delete_many(objs: tuple[M]) -> tuple[str, tuple[Any, ...]]:
    """called by delete_many methods

    Args:
        objs (tuple[M]): objects to delete

    Raises:
        IndexError: if the the obj tuple is empty
        BadQueryError: if the objects don't have either rowid or pks

    Returns:
        tuple[str, tuple[Any, ...]]
    """
    if not objs:
        raise IndexError('param "objs" is empty, pass at least one object')

    tablename = objs[0].__tablename__
    placeholders = ", ".join("?" * len(objs))
    if all(obj.__rowid__ for obj in objs):
        vals = tuple(obj.__rowid__ for obj in objs)
        q = f"DELETE FROM {tablename} WHERE rowid IN ({placeholders})"

    elif (pk := objs[0].__pk__) and all(getattr(o, pk, None) is not None for o in objs):
        vals = tuple(getattr(obj, pk) for obj in objs)
        q = f"DELETE FROM {tablename} WHERE id IN ({placeholders})"

    else:
        raise BadQueryError(
            "Objects requiere either a primary key or the rowid set for mass deletion"
        )

    log_query(q, vals)
    return q, vals


def for_count(tablename: str, column: str = '*', kws: Optional[dict] = None) -> tuple[str, tuple]:
    """Returns a query for counting the number of non null values in a column

    Args:
        tablename (str): The name of the table.
        column (str, optional): The column to count. . Defaults to '*' which then counts all the rows
        kws (dict, optional): The key/value pair for the "WHERE" clausule
            If not specified the complete table will be used.

    Returns:
        tuple: the query and vals
    """
    q = f'SELECT COUNT({column}) AS total_count FROM {tablename}'
    
    vals = ()
    if kws:
        keys, vals = zip(*kws.items())
        placeholders = ', '.join(f'{k} = ?' for k in keys)
        q += f' WHERE {placeholders};'
        
    return q, vals

