
from datetime import datetime, date
from pydantic import BaseModel


SCHEMA_TEMPLATE = 'CREATE TABLE IF NOT EXISTS {tablename} (\n{fields}\n);'


FIELD_MAPPING = {
    int: 'INTEGER',
    float: 'REAL',
    str: 'TEXT',
    bytes: 'BLOB',
    bool: 'INTEGER',
    date: 'DATE',
    datetime: 'TIMESTAMP'
}

def get_tablename(model: type[BaseModel]) -> str:
    return getattr(model, '__tablename__', model.__name__.lower())

def get_fields(model: type[BaseModel]) -> str:
    
    fields = []
    for field in model.__fields__.values():
        if field.type_ not in FIELD_MAPPING:
            raise TypeError(f'Unrecognized sqlite type "{field.type_}"')
        
        type_ = FIELD_MAPPING[field.type_]
        
        out = f'    {field.name} {type_}'
        if field.name == 'id' and type_ == 'INTEGER':
            out += ' PRIMARY KEY'
        if field.required and not out.endswith('KEY'):
            out += ' NOT NULL'
        if field.default is not None:
            out += f' DEFAULT {field.default!r}'
        
        fields.append(out)
        
    return ',\n'.join(fields)

def make_schema(Model: type[BaseModel]) -> str:
    return SCHEMA_TEMPLATE.format(
        tablename=get_tablename(Model),
        fields=get_fields(Model)
    )