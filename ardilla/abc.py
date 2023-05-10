from typing import Generic, Self, Literal
from abc import abstractmethod, ABC

from .errors import MissingEngine
from .engine import Engine
from .models import M, Model as BaseModel


class CrudABC(ABC):
    engine: Engine
    
    def __init__(self, Model: type[M], engine: Engine | None = None) -> None:
        if engine:
            self.engine = engine
        
        self.Model = Model
        if Model.__schema__:
            self.engine.schemas.add(Model.__schema__)
        self.tablename = Model.__tablename__
        self.columns = tuple(Model.__fields__)
    
    def __new__(cls, Model: type[M], engine: Engine | None = None) -> Self:
        if not issubclass(Model, BaseModel):
            raise TypeError('Model param has to be a subclass of model')
        
        cls_engine = getattr(cls, 'engine', None)
        
        if not isinstance(engine, Engine) and not isinstance(cls_engine, Engine):
            raise MissingEngine(
                "You must either set the engine at class level (Crud.engine = Engine(...))"
                "or pass it as an argument."
            )
        return super().__new__(cls)
        
    # Create
    @abstractmethod        
    def _do_insert(self, ignore: bool = False, returning: bool = True, / , **kws): pass
    
    @abstractmethod    
    def insert(self, **kws): pass
    
    @abstractmethod
    def insert_or_ignore(self): pass

    # Read
    @abstractmethod
    def get_all(self) -> list[M]: pass

    @abstractmethod
    def get_many(self, **kws) -> list[M]: pass

    @abstractmethod
    def get_or_create(self, **kws) -> tuple[M, bool]: pass

    @abstractmethod
    def get_or_none(self, **kws) -> M | None: pass
    
    @abstractmethod
    def _get_or_none_any(self, many: bool, **kws) -> list[M] | M | None: pass

    # Update
    @abstractmethod
    def save_one(self, obj: M) -> Literal[True]: pass
    
    @abstractmethod
    def save_many(self, *objs: M) -> Literal[True]: pass

    # Delete
    @abstractmethod
    def delete_one(self, obj: M) -> Literal[True]: pass

    @abstractmethod
    def delete_many(self, *objs: M) -> Literal[True]: pass


