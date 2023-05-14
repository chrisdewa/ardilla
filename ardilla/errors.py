class BaseArdillaException(Exception):
    pass


class ModelIntegrityError(BaseArdillaException):
    pass


class MissingEngine(BaseArdillaException):
    pass


class QueryExecutionError(BaseArdillaException):
    pass


class BadQueryError(BaseArdillaException):
    pass
