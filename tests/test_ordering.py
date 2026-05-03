import pytest

from ardilla.ordering import validate_ordering


def test_valid_ordering_returns_uppercase():
    columns = ("id", "name", "age")
    result = validate_ordering(columns, {"id": "asc", "name": "desc"})
    assert result == {"id": "ASC", "name": "DESC"}


def test_valid_ordering_already_uppercase():
    columns = ("id",)
    result = validate_ordering(columns, {"id": "DESC"})
    assert result == {"id": "DESC"}


def test_valid_ordering_mixed_case():
    columns = ("id",)
    assert validate_ordering(columns, {"id": "Asc"}) == {"id": "ASC"}
    assert validate_ordering(columns, {"id": "DeSc"}) == {"id": "DESC"}


def test_invalid_column_raises_key_error():
    columns = ("id", "name")
    with pytest.raises(KeyError):
        validate_ordering(columns, {"nonexistent": "ASC"})


def test_invalid_direction_raises_value_error():
    columns = ("id",)
    with pytest.raises(ValueError):
        validate_ordering(columns, {"id": "SIDEWAYS"})


def test_invalid_direction_empty_string_raises_value_error():
    columns = ("id",)
    with pytest.raises(ValueError):
        validate_ordering(columns, {"id": ""})


def test_empty_ordering_returns_empty_dict():
    result = validate_ordering(("id",), {})
    assert result == {}


def test_multiple_columns():
    columns = ("id", "name", "created_at")
    result = validate_ordering(columns, {"id": "asc", "created_at": "desc"})
    assert result == {"id": "ASC", "created_at": "DESC"}


def test_does_not_mutate_input():
    columns = ("id",)
    original = {"id": "asc"}
    result = validate_ordering(columns, original)
    assert original == {"id": "asc"}
    assert result == {"id": "ASC"}
