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


class DisconnectedEngine(ArdillaException):
    pass


disconnected_engine_error = DisconnectedEngine(
    "The engine has been disconnected and cannot operate on the database"
)
