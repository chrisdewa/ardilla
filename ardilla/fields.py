from pydantic import Field
from ardilla import Model

from .utils import SingletonMeta

class _ForeignFieldMaker(metaclass=SingletonMeta):
    """
    Helper class to generate foreing key field constrains.
    The class is a singleton. 
    The developer should use the instantiated `ardilla.fields.ForeignKey`
    instead of directly instantiating this class.
    
    Class Attributes
        NO_ACTION - The database won't take action. This most likely will result in errors
        RESTRICT - The app will not be able to delete the foreing row unless there's no related child elements left
        SET_NULL - The app will set the child to Null if the parent is deleted
        SET_DEFAULT - Returns the value of this field to the default of the child when the parent is deleted or updated
        CASCADE - If the parent gets deleted or updated the child follows
            
        
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
    ):
        """
        Args:
            references (type[Model]):
                The model this foreign key points to
            on_delete (str) defaults to 'NO ACTION':
                what happens when the referenced row gets deleted
            on_update (str) defaults to 'NO ACTION':
                what happens when the referenced row gets updated
        Returns:
            A `pydantic.Field` with extra metadata for the schema creation
        raises:
            KeyError if the referenced value is not a type of model
            ValueError if the referenced model does not have a primary key or has not yet been instantiated
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
        )

ForeignField = _ForeignFieldMaker()