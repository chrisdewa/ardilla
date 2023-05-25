from typing import Any
from pydantic import Field
from ardilla import Model

class _ForeignFieldMaker():
    """
    Helper class to generate foreing key field constrains.
    
    Intead of instantiating this class the developer should use 
    the already instantiated `ardilla.fields.ForeignKey`
    instead of directly instantiating this class.
    
    Attributes:
        NO_ACTION (str): (class attribute) The database won't take action. This most likely will result in errors
        RESTRICT (str): (class attribute) The app will not be able to delete the foreing row unless there's no related child elements left
        SET_NULL (str): (class attribute) The app will set the child to Null if the parent is deleted
        SET_DEFAULT (str): (class attribute) Returns the value of this field to the default of the child when the parent is deleted or updated
        CASCADE (str): (class attribute) If the parent gets deleted or updated the child follows  
        
    """
    NO_ACTION = 'NO ACTION'
    RESTRICT = 'RESTRICT'
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    CASCADE = 'CASCADE'
    
    def __call__(
        self,
        *,
        references: type[Model],
        on_delete: str = NO_ACTION, 
        on_update: str = NO_ACTION,
        **kws,
    ) -> Any:
        """
        Args:
            references (type[Model]):
                The model this foreign key points to
            on_delete (str): defaults to 'NO ACTION'
                what happens when the referenced row gets deleted
            on_update (str): defaults to 'NO ACTION'
                what happens when the referenced row gets updated
        Returns:
            A `pydantic.Field` with extra metadata for the schema creation
        Raises:
            KeyError: if the referenced value is not a type of model
            ValueError: if the referenced model does not have a primary key or has not yet been instantiated
        """
        if not issubclass(references, Model):
            raise TypeError('The referenced type must be a subclass of ardilla.Model')
        fk = getattr(references, '__pk__', None)
        tablename = getattr(references, '__tablename__')
        
        if not fk:
            raise ValueError('The referenced model requires to have a primary key')
        
        return Field(
            references=tablename, 
            fk=fk,
            on_delete=on_delete,
            on_update=on_update,
            **kws
        )

ForeignField = _ForeignFieldMaker()