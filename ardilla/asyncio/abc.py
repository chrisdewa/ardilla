from abc import ABC, abstractmethod
import aiosqlite

class AbstractAsyncEngine(ABC):
    """This just provides autocompletition across the library"""
    schemas: set[str]

    @abstractmethod
    async def __aenter__(self) -> aiosqlite.Connection:
        ...
    @abstractmethod
    async def cursor(self, con: aiosqlite.Connection) -> aiosqlite.Cursor:
        ...
    @abstractmethod
    async def connect(self) -> aiosqlite.Connection:
        ...