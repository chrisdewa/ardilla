from typing import Literal, Generic, Self

from .engine import Engine
from .abc import CrudABC
from .models import M, Model as BaseModel
from .errors import MissingEngine


class Crud(CrudABC, Generic[M]):
    """Abstracts CRUD actions for model associated tables"""

    def _get_or_none_any(self, many: bool, **kws):
        """
        private helper to the get_or_none queries.
        if param "many" is true it will return a list of matches else will return only one record
        """
        keys, vals = zip(*kws.items())
        to_match = f" AND ".join(f"{k} = ?" for k in keys)

        limit = 'LIMIT 1;' if not many else ';'
        q = f"SELECT * FROM {self.tablename} WHERE ({to_match}) {limit}"
        with self.engine as con:
            with self.engine.cursor(con) as cur:
                cur.execute(q, vals)
                if many:
                    result = cur.fetchall()
                    return [self.Model(**entry) for entry in result]
                else:
                    result = cur.fetchone()
                    if result:
                        return self.Model(**result)


    def get_or_none(self, **kws) -> M | None:
        """Gets an object from a database or None if not found"""
        return self._get_or_none_any(many=False, **kws)

    def insert_or_ignore(self, **kws) -> M | None:
        """inserts a the object of a row or ignores it if it already exists"""
        keys, vals = zip(*kws.items())
        placeholders = ", ".join("?" * len(keys))
        cols = ", ".join(keys)
        q = f"INSERT OR IGNORE INTO {self.tablename} ({cols}) VALUES ({placeholders}) RETURNING *;"
        with self.engine as con:
            with self.engine.cursor(con) as cur:
                cur.execute(q, vals)
                result = cur.fetchone()
                con.commit()
                if result:
                    return self.Model(**result)
        

    def get_or_create(self, **kws) -> tuple[M, bool]:
        """Returns object and bool indicated if it was created or not"""
        created = False
        result = self.get_or_none(**kws)
        if not result:
            result = self.insert_or_ignore(**kws)
            created = True
        return result, created

    def get_all(self) -> list[M]:
        """Gets all objects from the database"""
        q = f"SELECT * FROM {self.tablename};"
        with self.engine as con:
            with self.engine.cursor(con) as cur:
                cur.execute(q)
                results = cur.fetchall()
                return [self.Model(**res) for res in results]
        
    def get_many(self, **kws) -> list[M]:
        """Returns a list of objects that have the given conditions"""
        return self._get_or_none_any(many=True, **kws)

    def save_one(self, obj: M) -> Literal[True]:
        """Saves one object to the database"""
        cols, vals = zip(*obj.dict().items())
        placeholders = ", ".join("?" * len(cols))

        upsert_query = f"""
        INSERT OR REPLACE INTO {self.tablename} ({', '.join(cols)}) VALUES ({placeholders});
        """
        with self.engine as con:
            con.execute(upsert_query, vals)
            con.commit()
        return True

    def save_many(self, *objs: M) -> Literal[True]:
        """Saves all the given objects to the database"""
        placeholders = ", ".join("?" * len(self.columns))
        q = f'INSERT OR REPLACE INTO {self.tablename} ({", ".join(self.columns)}) VALUES ({placeholders});'
        vals = [tuple(obj.dict().values()) for obj in objs]
        with self.engine as con:
            con.executemany(q, vals)
            con.commit()
            
        return True

    def delete_one(self, obj: M) -> Literal[True]:
        """
        Deletes the object from the database (won't delete the actual object)
        queries only by the Model id fields (fields suffixed with 'id')
        """
        obj_dict = obj.dict()
        id_cols = tuple([k for k in obj_dict if "id" in k])
        placeholders = ", ".join(f"{k} = ?" for k in id_cols)
        vals = tuple([obj_dict[k] for k in id_cols])
        q = f"DELETE FROM {self.tablename} WHERE ({placeholders});"
        with self.engine as con:
            con.execute(q, vals)
            con.commit()
        
        return True

    def delete_many(self, *objs: M) -> Literal[True]:
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

        with self.engine as con:
            con.execute(q, vals)
            con.commit()

        return True