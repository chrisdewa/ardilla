from logging import getLogger
from typing import Callable

log = getLogger('ardilla')

def log_query(q: str, vals: tuple | None = None):
    vals = vals or ()
    log.info(f'Querying: {q} - values: {vals}')

