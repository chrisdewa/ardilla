from .errors import BadQueryError
from .models import M

QueryNVals = tuple[str, tuple]

def for_get_or_none_any(tablename: str, many: bool, kws) -> QueryNVals:
    keys, vals = zip(*kws.items())
    to_match = f" AND ".join(f"{k} = ?" for k in keys)
    limit = "LIMIT 1;" if not many else ";"
    q = f"SELECT rowid, * FROM {tablename} WHERE ({to_match}) {limit}"
    return q, vals


def for_do_insert(
    tablename: str,
    ignore: bool,
    returning: bool,
    kws,
) -> QueryNVals:
    keys, vals = zip(*kws.items())
    placeholders = ", ".join("?" * len(keys))
    cols = ", ".join(keys)

    q = "INSERT OR IGNORE " if ignore else "INSERT "
    q += f"INTO {tablename} ({cols}) VALUES ({placeholders})"
    q += " RETURNING *;" if returning else ";"
    return q, vals


def for_save_one(obj: M) -> QueryNVals:
    cols, vals = zip(*obj.dict().items())

    if obj.__rowid__ is not None:
        q = f"""
        UPDATE {obj.__tablename__} SET ({', '.join(f'{k} = ?' for k in cols)}) WHERE rowid = ?;
        """
        vals += obj.__rowid__

    else:
        placeholders = ", ".join("?" * len(cols))
        q = f"""
        INSERT OR REPLACE INTO {obj.__tablename__} ({', '.join(cols)}) VALUES ({placeholders});
        """
    return q, vals

def for_save_many(objs: tuple[M]) -> QueryNVals:
    if not objs:
        raise BadQueryError('To save many, you have to at least past one object')
    cols = tuple(objs[0].__fields__)
    tablename = objs[0].__tablename__
    placeholders = ", ".join("?" * len(cols))
    q = f'INSERT OR REPLACE INTO {tablename} ({", ".join(cols)}) VALUES ({placeholders});'
    vals = [tuple(obj.dict().values()) for obj in objs]
    return q, vals

def for_delete_one(obj: M) -> QueryNVals:
    tablename = obj.__tablename__
    if obj.__pk__:
        q = f'DELETE FROM {tablename} WHERE {obj.__pk__} = ?'
        vals = getattr(obj, obj.__pk__),
    elif obj.__rowid__:
        q = f'DELETE FROM {tablename} WHERE rowid = ?'
        vals = obj.__rowid__,
    else:
        obj_dict = obj.dict()
        id_cols = tuple([k for k in obj_dict if "id" in k])
        placeholders = ", ".join(f"{k} = ?" for k in id_cols)
        vals = tuple([obj_dict[k] for k in id_cols])
        q = f"""
        DELETE FROM {tablename} WHERE ({placeholders});
        """
    return q, vals

def for_delete_many(objs: tuple[M]) -> QueryNVals:
    if not objs:
        raise IndexError('param "objs" is empty, pass at least one object')

    tablename = objs[0].__tablename__
    placeholders = ', '.join('?' for _ in objs)
    if all(obj.__rowid__ for obj in objs):
        vals = [obj.__rowid__ for obj in objs]    
        q = f'DELETE FROM {tablename} WHERE rowid IN ({placeholders})'

    elif pk := objs[0].__pk__:
        vals = [getattr(obj, pk) for obj in objs]
        q = f'DELETE FROM {tablename} WHERE id IN ({placeholders})'
        
    else:
        raise BadQueryError('Objects requiere either a primary key or the rowid set for mass deletion')
    
    return q, vals