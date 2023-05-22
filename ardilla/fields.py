from pydantic import Field
from ardilla import Model


class _ForeignFieldMaker:
    NO_ACTION = 'NO ACTION'
    RESTRICT = 'RESTRICT'
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    CASCADE = 'CASCADE'
    
    def __call__(
        self,
        *,
        references: Model,
        on_delete: str = NO_ACTION, 
        on_update: str = NO_ACTION,
    ):
        fk = getattr(references, '__pk__', None)
        tablename = getattr(references, '__tablename__', None)
        if not fk:
            raise ValueError('The referenced model requires to have a primary key')
        elif not tablename:
            raise ValueError('The referenced model does not have a tablename')
        return Field(
            references=tablename, 
            fk=fk,
            on_delete=on_delete,
            on_update=on_update,
        )

ForeignField = _ForeignFieldMaker()