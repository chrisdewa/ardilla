from logging import getLogger
from typing import Optional

log = getLogger('ardilla')

def log_query(q: str, vals:  Optional[tuple] = None):
    vals = vals or ()
    log.debug(f'Querying: {q} - values: {vals}')

