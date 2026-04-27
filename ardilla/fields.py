from typing import Any
from pydantic import Field as _PydanticField


_ARDILLA_KEYS = {'pk', 'primary', 'primary_key', 'auto', 'unique',
                 'references', 'fk', 'on_delete', 'on_update'}


def Field(
    default=...,
    *,
    pk: bool = False,
    primary: bool = False,
    primary_key: bool = False,
    auto: bool = False,
    unique: bool = False,
    **kwargs,
) -> Any:
    """pydantic Field extended with ardilla schema metadata.

    Ardilla-specific kwargs are stored in json_schema_extra so pydantic v2
    sees them without deprecation warnings. Fields marked auto=True get
    default=None so instances can be constructed without supplying the value.
    """
    extra: dict = {}
    if pk:
        extra['pk'] = True
    if primary:
        extra['primary'] = True
    if primary_key:
        extra['primary_key'] = True
    if auto:
        extra['auto'] = True
        if default is ...:
            default = None
    if unique:
        extra['unique'] = True

    if extra:
        existing = kwargs.pop('json_schema_extra', {}) or {}
        kwargs['json_schema_extra'] = {**existing, **extra}

    return _PydanticField(default, **kwargs)


class _ForeignFieldMaker:
    """
    Helper class to generate foreign key field constraints.

    Use the pre-instantiated `ardilla.fields.ForeignField` rather than
    instantiating this class directly.

    Attributes:
        NO_ACTION: The database won't take action.
        RESTRICT: Prevents deletion while child rows exist.
        SET_NULL: Sets child FK to NULL on parent delete.
        SET_DEFAULT: Resets child FK to its default on parent delete/update.
        CASCADE: Propagates delete/update from parent to children.
    """
    NO_ACTION = 'NO ACTION'
    RESTRICT = 'RESTRICT'
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    CASCADE = 'CASCADE'

    def __call__(
        self,
        *,
        references: type,
        on_delete: str = NO_ACTION,
        on_update: str = NO_ACTION,
        **kws,
    ) -> Any:
        """
        Args:
            references: The Model subclass this foreign key points to.
            on_delete: Action when the referenced row is deleted. Defaults to 'NO ACTION'.
            on_update: Action when the referenced row is updated. Defaults to 'NO ACTION'.
        Returns:
            A pydantic Field with FK metadata in json_schema_extra.
        Raises:
            TypeError: if references is not a subclass of ardilla.Model.
            ValueError: if the referenced model has no primary key.
        """
        from ardilla.models import Model
        if not issubclass(references, Model):
            raise TypeError('The referenced type must be a subclass of ardilla.Model')
        fk = getattr(references, '__pk__', None)
        tablename = getattr(references, '__tablename__')

        if not fk:
            raise ValueError('The referenced model requires a primary key')

        extra = {
            'references': tablename,
            'fk': fk,
            'on_delete': on_delete,
            'on_update': on_update,
        }
        existing = kws.pop('json_schema_extra', {}) or {}
        kws['json_schema_extra'] = {**existing, **extra}
        return _PydanticField(**kws)


ForeignField = _ForeignFieldMaker()
