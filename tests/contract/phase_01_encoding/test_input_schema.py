import pytest
from jsonschema import Draft202012Validator

from tests._utils.helpers.contracts import load_schema


pytestmark = pytest.mark.contract


def test_phase_01_input_schema_is_valid():
    sch = load_schema("phase_01_encoding", "input")
    Draft202012Validator.check_schema(sch)
    assert "$id" in sch and isinstance(sch["$id"], str)
