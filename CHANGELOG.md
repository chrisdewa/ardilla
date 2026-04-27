# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.5.0-beta] - 2026-04-27

### Added

- `ardilla.Field` — a custom wrapper around `pydantic.Field` that accepts
  ardilla-specific keyword arguments (`pk`, `primary`, `primary_key`, `auto`,
  `unique`) directly, storing them in `json_schema_extra` so pydantic v2 sees
  them without deprecation warnings. Fields declared with `auto=True` now
  automatically receive `default=None`, meaning model instances can be
  constructed without supplying the auto-generated value.
- `is_nullable()` helper in `ardilla.types` — detects whether a type
  annotation allows `None` (i.e. `Optional[T]` / `T | None`), used by the
  schema generator to correctly omit `NOT NULL` for nullable columns.
- Python 3.12 and 3.13 classifiers in `pyproject.toml`.

### Changed

- **Pydantic v1 → v2**: minimum pydantic version raised from `1.10.7` to
  `>=2.0`. The library now targets the pydantic v2 API exclusively.
- `__pk__`, `__tablename__`, and `__schema__` on `ardilla.Model` are now
  declared as `ClassVar` so pydantic v2 does not attempt to treat them as
  model fields.
- `_row2obj` in `BaseCrud` now uses `object.__setattr__` to assign `__rowid__`
  on model instances, bypassing pydantic v2's `__setattr__` validation for
  attributes that are not model fields.
- `make_field_schema` in `ardilla.schemas` no longer mutates `FieldInfo.default`
  at runtime (a no-op in pydantic v2 once the schema is compiled). Auto-field
  defaults are now handled upfront by the custom `Field` wrapper.
- `Optional[T]` fields without an explicit default are no longer marked
  `NOT NULL` in generated table schemas. Previously this relied on pydantic v1
  treating `Optional` fields as implicitly optional; pydantic v2 requires an
  explicit default for that, but the SQLite schema should still be nullable.
- `for_save_many` in `ardilla.queries` now accesses `model_fields` via the
  class (`type(obj).model_fields`) rather than the instance, fixing a
  deprecation warning introduced in pydantic v2.11.
- `ForeignField` routes its metadata (`references`, `fk`, `on_delete`,
  `on_update`) through `json_schema_extra` instead of bare extra kwargs.
- `types.UnionType` (the runtime type of `X | Y` union syntax) is now guarded
  behind a `sys.version_info >= (3, 10)` check, restoring Python 3.9
  compatibility.
- Dependency versions bumped: `aiosqlite>=0.19`, `fastapi>=0.100`,
  `uvicorn>=0.23`, `pytest>=7.4`, `pytest-asyncio>=0.23`, `black>=24`,
  `mkdocs>=1.5`, `mkdocstrings[python]>=0.24`.
- Package manager migrated from poetry to **uv**.

### Fixed

- `generate_migration_script` raised `NameError: name 'tablename' is not
  defined` when `new_tablename` was provided, because `tablename` was
  referenced before assignment. Fixed to use `original_tablename`.

### Removed

- Direct dependency on pydantic v1. The `pydantic_core` import of
  `PydanticUndefined` remains (it is part of pydantic v2's public API).
- Unused `from pydantic import Json` import from `ardilla.schemas` and tests.

---

## [0.4.0-beta] - 2023-05-xx

### Added

- `Crud.count` and `AsyncCrud.count` methods.
- Migration script generator (`ardilla.migration.generate_migration_script`).
- Test coverage for migration scripts.

### Changed

- `pyproject.toml` examples extra updated.

---

## [0.3.x and earlier]

Legacy releases under pydantic v1. See git history for details.
