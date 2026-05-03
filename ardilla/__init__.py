import sqlite3
from datetime import date, time, datetime as _datetime

# Python 3.12+ deprecated the default date/time adapters; 3.14 removed the
# time adapter entirely.  Register explicit ISO-format adapters so all three
# types round-trip correctly on every supported Python version.
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(time, lambda t: t.isoformat())
sqlite3.register_adapter(_datetime, lambda dt: dt.isoformat(sep=" "))

from .engine import Engine as Engine
from .models import Model as Model
from .crud import Crud as Crud
from .fields import Field, ForeignField