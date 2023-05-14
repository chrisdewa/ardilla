"""
Contains the module's errors
"""

class ArdillaException(Exception):
    pass


class ModelIntegrityError(ArdillaException):
    pass


class MissingEngine(ArdillaException):
    pass


class QueryExecutionError(ArdillaException):
    pass


class BadQueryError(ArdillaException):
    pass
