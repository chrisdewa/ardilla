"""
Contains the Model object and typing alias to work with the engines and Cruds
"""
from typing import Optional, TypeVar, get_origin
from pydantic import BaseModel

from . import types
from .schemas import make_table_schema, get_tablename, get_pk
from .errors import ModelIntegrityError



class Model(BaseModel):
    """
    The base model representing SQLite tables
    Inherits directly from pydantic.BaseModel
    
    Attributes:
        __rowid__ (int | None): (class attribute) when an object is returned by a query it will 
            contain the rowid field that can be used for update and deletion.
        __pk__ (str | None): (class attribute) Holds the primary key column name of the table
        __tablename__ (str): (class attribute) the name of the table in the database
        __schema__(str): the (class attribute) schema for the table.
        
    Example:
        ```py
        from ardilla import Model, Field
        # Field is actually pydantic.Field but it's imported here for the convenience of the developer
        
        class User(Model):
            __tablename__ = 'users' # by default the tablename is just the model's name in lowercase
            id: int = Field(primary=True) # sets this field as the primary key
            name: str
        ```
    """
    __rowid__: Optional[int] = None
    __pk__: Optional[str]  # tells the model which key to idenfity as primary
    __tablename__: str  # will default to the lowercase name of the subclass
    __schema__: str  # best effort will be made if it's missing
    # there's no support for constrains or foreign fields yet but you can
    # define your own schema to support them

    @classmethod
    def __pydantic_init_subclass__(cls, **kws) -> None:
        for name, field in cls.model_fields.items():
            if not types.check_type_annotation(field.annotation):
                raise ModelIntegrityError(
                    f'Field "{name}" of model "{cls.__name__}" is of unsupported type "{field.annotation}"'
                )

            if (
                field.json_schema_extra 
                and field.json_schema_extra.keys() 
                    & {'primary', 'primary_key', 'pk'}
            ):
                if getattr(cls, '__pk__', None) not in {None, name}:
                    raise ModelIntegrityError('More than one fields defined as primary')
                
                cls.__pk__ = name 
                
        if not hasattr(cls, "__schema__"):
            cls.__schema__ = make_table_schema(cls)
        
        if not hasattr(cls, '__pk__'):
            cls.__pk__ = get_pk(cls.__schema__)

        if not hasattr(cls, "__tablename__"):
            tablename = get_tablename(cls)
            setattr(cls, "__tablename__", tablename)

        # super().__post_init__(**kws)

    def __str__(self) -> str:
        return f"{self!r}"


M = TypeVar("M", bound=Model)
