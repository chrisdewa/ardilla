# changelog

The changelog started on version 0.4.0-beta.

## changes:

<hr>
**0.5.0-beta:** Migrated to Pydantic v2.

- `ardilla.Field` is now a wrapper function (not a re-export of `pydantic.Field`). Ardilla-specific kwargs (`pk`, `primary`, `primary_key`, `auto`, `unique`) are stored in `json_schema_extra`.
- `pk`, `primary`, and `primary_key` are now all valid and equivalent aliases for marking a primary key field.
- Fields with `auto=True` automatically receive `default=None`; do not combine with `default_factory`.
- `__pk__`, `__tablename__`, and `__schema__` are now `ClassVar` (not pydantic `PrivateAttr`). `__rowid__` is a regular optional model field.
- Internal schema inspection uses `model_fields` and `field.json_schema_extra` (pydantic v2 API).
- Build system migrated from `poetry` to `uv`.
<hr>
**0.4.0-beta:** Added a migration script generator. Improved schema generation.
<hr>