import pytest

from core.validation import validate_input, validate_output, ValidationError
from tests._utils.helpers.contracts import cross_field_checks
from tests._utils.factories import (
    make_phase01_input_minimal,
    make_phase01_input_invalid,
    make_phase01_output_ok,
)


pytestmark = pytest.mark.component


def test_validate_input_minimal_ok():
    payload = make_phase01_input_minimal()
    cross_field_checks(payload, "phase_01_encoding.input")
    validate_input("phase_01_encoding", payload)


def test_validate_input_invalid_raises():
    payload = make_phase01_input_invalid()
    with pytest.raises(ValidationError):
        validate_input("phase_01_encoding", payload)


def test_validate_output_ok():
    payload = make_phase01_output_ok()
    cross_field_checks(payload, "phase_01_encoding.output")
    validate_output("phase_01_encoding", payload)
