from __future__ import annotations

from typing import TYPE_CHECKING
from pydantic import Field as _PydanticField
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

if TYPE_CHECKING:
    from ardilla.models import Model

_PK_KEYS: frozenset[str] = frozenset({"pk", "primary", "primary_key"})


def Field(
    default=PydanticUndefined,
    *,
    pk: bool = False,
    primary: bool = False,
    primary_key: bool = False,
    auto: bool = False,
    unique: bool = False,
    **kwargs,
) -> FieldInfo:
    """Pydantic Field extended with ardilla schema metadata.

    Args:
        default: Default value for the field. Omit (or pass ``...``) to mark
            the field as required. Fields with ``auto=True`` default to ``None``
            unless an explicit default is provided.
        pk: Mark this field as the primary key (alias for ``primary_key``).
        primary: Mark this field as the primary key (alias for ``primary_key``).
        primary_key: Mark this field as the primary key.
        auto: Exclude this field from INSERT statements so the database
            populates it automatically (e.g. AUTOINCREMENT, DEFAULT).
        unique: Add a UNIQUE constraint to this column.
        **kwargs: Forwarded verbatim to :func:`pydantic.Field`.

    Returns:
        A :class:`pydantic.fields.FieldInfo` with ardilla metadata stored in
        ``json_schema_extra``.

    Example:
        ```py
        from ardilla import Model, Field

        class User(Model):
            id: int = Field(pk=True, auto=True)
            name: str = Field(unique=True)
        ```
    """
    flags = {"pk": pk, "primary": primary, "primary_key": primary_key, "unique": unique}
    extra = {name: True for name, val in flags.items() if val}

    if auto:
        extra["auto"] = True
        if default is PydanticUndefined or default is ...:
            default = None

    if extra:
        existing = kwargs.pop("json_schema_extra", {}) or {}
        kwargs["json_schema_extra"] = {**existing, **extra}

    return _PydanticField(default, **kwargs)


class ForeignField(FieldInfo):
    """
    FieldInfo subclass for foreign key columns.
    Inherits from pydantic.fields.FieldInfo.

    Attributes:
        references (type[Model]): The Model subclass this FK points to.
        on_delete (str): Action when the referenced row is deleted. Defaults to NO_ACTION.
        on_update (str): Action when the referenced row is updated. Defaults to NO_ACTION.
        NO_ACTION (str): The database won't take action.
        RESTRICT (str): Prevents deletion while child rows exist.
        SET_NULL (str): Sets child FK to NULL on parent delete/update.
        SET_DEFAULT (str): Resets child FK to its default on parent delete/update.
        CASCADE (str): Propagates delete/update from parent to children.

    Example:
        ```py
        from ardilla import Model, Field, ForeignField

        class Post(Model):
            id: int = Field(primary=True)

        class Comment(Model):
            post_id: int = ForeignField(references=Post, on_delete=ForeignField.CASCADE)
        ```
    """

    NO_ACTION = "NO ACTION"
    RESTRICT = "RESTRICT"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    CASCADE = "CASCADE"

    def __init__(
        self,
        *,
        references: "type[Model]",
        on_delete: str = NO_ACTION,
        on_update: str = NO_ACTION,
        **kwargs,
    ) -> None:
        from ardilla.models import Model  # avoid circular import

        if not issubclass(references, Model):
            raise TypeError("The referenced type must be a subclass of ardilla.Model")
        if not getattr(references, "__pk__", None):
            raise ValueError("The referenced model requires a primary key")

        self.references = references
        self.on_delete = on_delete
        self.on_update = on_update

        super().__init__(**kwargs)
