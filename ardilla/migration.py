from typing import Optional


from .models import Model
from .errors import MigrationError
from .schemas import make_field_schema, make_table_schema



def generate_migration_script(
    old: type[Model],
    new: type[Model],
    *,
    original_tablename: str,
    new_tablename: Optional[str] = None
) -> str:
    """_summary_

    Args:
        old (type[Model]): the old model
        new (type[Model]): the new model
        original_tablename (str): the tablename as it is in the database before migrating
        new_tablename (Optional[str], optional): If the table should change its name this is the new one. Defaults to None.

    Raises:
        MigrationError: Migration includes a new field with unique constraint
        MigrationError: Migration includes a new field with primary key constraint
        MigrationError: Migration includes a not null field without a default value

    Returns:
        str: The migration script. Execute it with an sqlite3 connection
    """      
    scripts = []

    if new_tablename is not None:
        scripts.append(
            f"ALTER TABLE {original_tablename} RENAME TO {new_tablename};"
        )
    
    tablename = tablename if not new_tablename else new_tablename

    old_fields = set(old.model_fields)
    new_fields = set(new.model_fields)

    dropped = old_fields - new_fields
    for field_name in dropped:
        scripts.append(f"ALTER TABLE {tablename} DROP COLUMN {field_name};")

    added = new_fields - old_fields
    for field_name in added:
        field = new.model_fields[field_name]
        schema = make_field_schema(field_name, field)
        if schema["unique"]:
            raise MigrationError(
                f"cannot process '{field_name}' because it's marked as unique"
            )
            continue
        if schema["pk"]:
            raise MigrationError(
                f"cannot process '{field_name}' because it's marked as primary key"
            )
        field_schema = schema["schema"]
        if "NOT NULL" in field_schema and not "DEFAULT" in field_schema:
            raise MigrationError(
                f'Cannot script a "not null" field without default value in field "{field_name}"'
            )

        scripts.append(f"ALTER TABLE {tablename} ADD COLUMN {field_schema};")

    conserved = old_fields & new_fields
    alter_fields = False
    for f in conserved:
        old_schema = make_field_schema(f, old.model_fields[f])
        new_schema = make_field_schema(f, new.model_fields[f])
        if old_schema != new_schema:
            alter_fields = True
            
            # if old.model_fields[f].type_ != new.model_fields[f].type_:
            #     print(
            #         f"Ardilla can't handle type changes for now. "
            #         f"You'll have to migrate this on your own."
            #     )
            #     alter_fields = False
            #     break

    if alter_fields is True:
        new_table_schema = make_table_schema(new)
        cols = ', '.join(name for name in new.model_fields)

        script = f'''
        \rALTER TABLE {tablename} RENAME TO _{tablename};
        \r
        \r{new_table_schema}
        \r
        \rINSERT INTO {tablename} ({cols})
        \r  SELECT {cols}
        \r  FROM _{tablename};
        \r
        \rDROP TABLE _{tablename};
        \r'''

        scripts.append(script)
        

    return "\n\n".join(scripts)

