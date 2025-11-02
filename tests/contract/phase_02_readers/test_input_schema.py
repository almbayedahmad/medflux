import pytest
from jsonschema import Draft202012Validator

from tests._utils.helpers.contracts import load_schema


pytestmark = pytest.mark.contract


def test_phase_02_input_schema_is_valid():
    sch = load_schema("phase_02_readers", "input")
    Draft202012Validator.check_schema(sch)
    assert "$id" in sch and isinstance(sch["$id"], str)
