from typing import Generic, Self
from abc import abstractmethod, ABC

from .errors import MissingEngine
from .engine import Engine
from .models import M, Model as BaseModel


class CrudABC(ABC):
    engine: Engine = None
    
    def __init__(self, Model: M, engine: Engine | None = None) -> None:
        if engine:
            self.engine = engine
        self.Model = Model
        if Model.__schema__:
            self.engine.schemas.add(Model.__schema__)
        self.tablename = Model.__tablename__
        self.columns = tuple(Model.__fields__)
    
    def __new__(cls, Model: M, engine: Engine | None = None) -> Self:
        if not issubclass(Model, BaseModel):
            raise TypeError('Model param has to be a subclass of model')
        
        if not isinstance(engine, Engine) and not isinstance(cls.engine, Engine):
            raise MissingEngine(
                "You must either set the engine at class level (Crud.engine = Engine(...))"
                "or pass it as an argument."
            )
        return super().__new__(cls)
        
    # Create
    @abstractmethod
    def insert_or_ignore(self): pass

    # Read
    @abstractmethod
    def get_all(self): pass

    @abstractmethod
    def get_many(self): pass

    @abstractmethod
    def get_or_create(self): pass

    @abstractmethod
    def get_or_none(self): pass
    
    @abstractmethod
    def _get_or_none_any(self): pass

    # Update
    @abstractmethod
    def save_one(self): pass
    
    @abstractmethod
    def save_many(self): pass

    # Delete
    @abstractmethod
    def delete_one(self): pass

    @abstractmethod
    def delete_many(self): pass


