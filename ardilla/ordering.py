from typing import Container

def validate_ordering(columns: Container[str], order_by: dict[str, str]) -> dict[str, str]:
    """validates an ordering dictionary
    The ordering should have this structure:
        {
            'column_name': 'ASC' OR 'DESC'
        }
    Case in values is insensitive
    
    Args:
        columns (Container[str]): a collection of columns to check the keys against
        order_by (dict[str, str]): 

    Raises:
        KeyError: if the key is not listed in the columns of the table
        ValueError: if the value is not either ASC or DESC

    Returns:
        dict[str, str]: a copy of the ordering dict with values in uppercase
    """
    out = order_by.copy()
    for k, v in order_by.items():
        if k not in columns:
            raise KeyError(f'"{k}" is not a valid column name')
        elif v.lower() not in {'desc', 'asc'}:
            raise ValueError(f'"{k}" value "{v}" is invalid, must be either "asc" or "desc" (case insensitive)')
        else:
            out[k] = v.upper()
    return out