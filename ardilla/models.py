from typing import TypeVar, Annotated
from pydantic import BaseModel, PrivateAttr

from .schemas import make_schema, FIELD_MAPPING, get_tablename, get_pk
from .errors import ModelIntegrityError


class Model(BaseModel):
    __rowid__: int | None = PrivateAttr(default=None)
    __pk__: str | None # tells the model which key to idenfity as primary
    __tablename__: str  # will default to the lowercase name of the subclass
    __schema__: str  # best effort will be made if it's missing
    # there's no support for constrains or foreign fields yet but you can
    # define your own schema to support them

    def __init_subclass__(cls, **kws) -> None:
        for field in cls.__fields__.values():
            if field.type_ not in FIELD_MAPPING:
                raise ModelIntegrityError(
                    f'Field "{field.name}" of model "{cls.__name__}" is of unsupported type "{field.type_}"'
                )


        if not hasattr(cls, "__schema__"):
            cls.__schema__ = make_schema(cls)
        
        cls.__pk__ = get_pk(cls.__schema__)

        if not hasattr(cls, "__tablename__"):
            tablename = get_tablename(cls)
            setattr(cls, "__tablename__", tablename)

        super().__init_subclass__(**kws)

    def __str__(self) -> str:
        return f"{self!r}"

    @property
    def has_pk(self) -> bool:
        return 'primary key' in self.__schema__.lower()

M = TypeVar("M", bound=Model)
