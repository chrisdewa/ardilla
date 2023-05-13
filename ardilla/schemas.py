import re
from datetime import datetime, date
from pydantic import BaseModel, Json
from .errors import ModelIntegrityError


SCHEMA_TEMPLATE = "CREATE TABLE IF NOT EXISTS {tablename} (\n{fields}\n);"


FIELD_MAPPING = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
    bool: "INTEGER",
    date: "DATE",
    datetime: "TIMESTAMP",
    Json: "TEXT",
}


def get_tablename(model: type[BaseModel]) -> str:
    return getattr(model, "__tablename__", model.__name__.lower())


def get_fields(model: type[BaseModel]) -> str:
    fields = []
    for field in model.__fields__.values():
        if field.type_ not in FIELD_MAPPING:
            raise TypeError(f'Unrecognized sqlite type "{field.type_}"')

        type_ = FIELD_MAPPING[field.type_]
        pk = getattr(model, "__pk__", None)
        field_is_pk = field.field_info.extra.get(
            "primary"
        ) or field.field_info.extra.get("primary_key")
        if field_is_pk and pk and field.name != pk:
            raise ModelIntegrityError(
                f"field {field.name} is marked as pk, but __pk__ points to other field."
            )
        out = f"    {field.name} {type_}"
        if pk == field.name or field_is_pk:
            out += " PRIMARY KEY"
            if field.field_info.extra.get("autoincrement"):
                out += " AUTOINCREMENT"
        if field.required and not "PRIMARY KEY" in out:
            out += " NOT NULL"
        if field.default is not None:
            out += f" DEFAULT {field.default!r}"

        fields.append(out)

    return ",\n".join(fields)


def make_schema(Model: type[BaseModel]) -> str:
    return SCHEMA_TEMPLATE.format(
        tablename=get_tablename(Model), fields=get_fields(Model)
    )


def get_pk(schema: str) -> str | None:
    # Check if the schema contains a primary key definition
    if "PRIMARY KEY" in schema:
        # Use a regular expression to extract the primary key column name
        match = re.search(r"(?i)\b(\w+)\b\s+(?:\w+\s+)*PRIMARY\s+KEY", schema)
        if match:
            return match.group(1)
