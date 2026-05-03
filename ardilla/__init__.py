import sqlite3
from datetime import date, time, datetime as _datetime

# register adapters for compatibility with older python
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(time, lambda t: t.isoformat())
sqlite3.register_adapter(_datetime, lambda dt: dt.isoformat(sep=" "))

from .engine import Engine as Engine
from .models import Model as Model
from .crud import Crud as Crud
from .fields import Field as Field, ForeignField as ForeignField
