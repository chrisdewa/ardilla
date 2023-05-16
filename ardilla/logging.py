from logging import getLogger

log = getLogger('ardilla')

def log_query(q: str, vals: tuple | None = None):
    vals = vals or ()
    log.debug(f'Querying: {q} - values: {vals}')

