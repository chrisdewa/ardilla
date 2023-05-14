"""
Methods here are used by Crud classes to obtain the query 
strings and variable tuples to pass to the connections and cursors
"""
from typing import Any
from .errors import BadQueryError
from .models import M

Query = str
Vals = tuple[Any, ...]


def for_get_or_none_any(tablename: str, many: bool, kws: dict) -> tuple[Query, Vals]:
    """called by _get_or_none_any methods

    Args:
        tablename (str): name of the table
        many (bool): if the function will return a single item or any amount
        kws (dict): the keywords to identify the rows with

    Returns:
        tuple[Query, Vals]: the query and values.
    """
    keys, vals = zip(*kws.items())
    to_match = f" AND ".join(f"{k} = ?" for k in keys)
    limit = "LIMIT 1;" if not many else ";"
    q = f"SELECT rowid, * FROM {tablename} WHERE ({to_match}) {limit}"
    return q, vals


def for_do_insert(
    tablename: str,
    ignore: bool,
    returning: bool,
    kws: dict,
) -> tuple[Query, Vals]:
    """called by _do_insert methods

    Args:
        tablename (str): name of the table
        ignore (bool): whether or not to use `INSERT OR IGNORE` vs just `INSERT`
        returning (bool): if the inserted values should be returned by the query
        kws (dict): the keywords representing column name and values

    Returns:
        tuple[Query, Vals]: the queries and values
    """
    keys, vals = zip(*kws.items())
    placeholders = ", ".join("?" * len(keys))
    cols = ", ".join(keys)

    q = "INSERT OR IGNORE " if ignore else "INSERT "
    q += f"INTO {tablename} ({cols}) VALUES ({placeholders})"
    q += " RETURNING *;" if returning else ";"
    return q, vals


def for_save_one(obj: M) -> tuple[Query, Vals]:
    """called by save_one methods

    Args:
        obj (M): the Model instance to save

    Returns:
        tuple[Query, Vals]: the query and values
    """    
    cols, vals = zip(*obj.dict().items())

    if obj.__rowid__ is not None:
        q = f"""
        UPDATE {obj.__tablename__} SET {', '.join(f'{k} = ?' for k in cols)} WHERE rowid = ?;
        """
        vals += obj.__rowid__,

    else:
        placeholders = ", ".join("?" * len(cols))
        q = f"""
        INSERT OR REPLACE INTO {obj.__tablename__} ({', '.join(cols)}) VALUES ({placeholders});
        """
    return q, vals

def for_save_many(objs: tuple[M]) -> tuple[Query, Vals]:
    """called by save_many methods

    Args:
        objs (tuple[M]): the objects to save

    Raises:
        BadQueryError: if the objs tuple is empty

    Returns:
        tuple[Query, Vals]: the query and values
    """
    if not objs:
        raise BadQueryError('To save many, you have to at least past one object')
    cols = tuple(objs[0].__fields__)
    tablename = objs[0].__tablename__
    placeholders = ", ".join("?" * len(cols))
    q = f'INSERT OR REPLACE INTO {tablename} ({", ".join(cols)}) VALUES ({placeholders});'
    vals = tuple(tuple(obj.dict().values()) for obj in objs)
    return q, vals

def for_delete_one(obj: M) -> tuple[Query, Vals]:
    """called by delete_one methods

    Args:
        obj (M): the object to delete

    Returns:
        tuple[Query, Vals]: the query and values
    """    
    tablename = obj.__tablename__
    if obj.__pk__:
        q = f'DELETE FROM {tablename} WHERE {obj.__pk__} = ?'
        vals = getattr(obj, obj.__pk__),
    elif obj.__rowid__:
        q = f'DELETE FROM {tablename} WHERE rowid = ?'
        vals = obj.__rowid__,
    else:
        obj_dict = obj.dict()
        placeholders = " AND ".join(f"{k} = ?" for k in obj_dict)
        vals = tuple(obj_dict[k] for k in obj_dict)
        q = f"""
        DELETE FROM {tablename} WHERE ({placeholders});
        """
    return q, vals

def for_delete_many(objs: tuple[M]) -> tuple[Query, Vals]:
    """called by delete_many methods

    Args:
        objs (tuple[M]): objects to delete

    Raises:
        IndexError: if the the obj tuple is empty
        BadQueryError: if the objects don't have either rowid or pks

    Returns:
        tuple[Query, Vals]: _description_
    """
    if not objs:
        raise IndexError('param "objs" is empty, pass at least one object')

    tablename = objs[0].__tablename__
    placeholders = ', '.join('?' for _ in objs)
    if all(obj.__rowid__ for obj in objs):
        vals = tuple(obj.__rowid__ for obj in objs)
        q = f'DELETE FROM {tablename} WHERE rowid IN ({placeholders})'

    elif pk := objs[0].__pk__:
        vals = tuple(getattr(obj, pk) for obj in objs)
        q = f'DELETE FROM {tablename} WHERE id IN ({placeholders})'
        
    else:
        raise BadQueryError('Objects requiere either a primary key or the rowid set for mass deletion')
    
    return q, vals