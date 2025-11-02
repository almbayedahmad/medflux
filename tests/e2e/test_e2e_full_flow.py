import pytest

from fastapi.testclient import TestClient

from backend.api.main import create_app
from core.validation import validate_input, validate_output
from tests._utils.factories import (
    make_phase00_input_minimal,
    make_phase00_output_ok,
    make_phase01_input_minimal,
    make_phase01_output_ok,
    make_phase02_input_minimal,
    make_phase02_output_ok,
)
from tests._utils.helpers.contracts import cross_field_checks


pytestmark = pytest.mark.e2e


def test_e2e_api_health_and_version_headers():
    app = create_app()
    client = TestClient(app)

    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
    # Verify correlation header is present
    assert "x-request-id" in r.headers

    r2 = client.get("/api/v1/version")
    assert r2.status_code == 200
    data = r2.json()
    assert isinstance(data.get("app", {}).get("version"), str)


def test_e2e_validation_flow_across_phases():
    # Use a single run_id across the mini flow
    run_id = "20250101T120000-deadbeef"

    # Phase 00: detect_type
    p00_in = make_phase00_input_minimal()
    p00_in["run_id"] = run_id
    cross_field_checks(p00_in, "phase_00_detect_type.input")
    validate_input("phase_00_detect_type", p00_in)

    p00_out = make_phase00_output_ok()
    p00_out["run_id"] = run_id
    cross_field_checks(p00_out, "phase_00_detect_type.output")
    validate_output("phase_00_detect_type", p00_out)

    # Phase 01: encoding
    p01_in = make_phase01_input_minimal()
    p01_in["run_id"] = run_id
    cross_field_checks(p01_in, "phase_01_encoding.input")
    validate_input("phase_01_encoding", p01_in)

    p01_out = make_phase01_output_ok()
    p01_out["run_id"] = run_id
    cross_field_checks(p01_out, "phase_01_encoding.output")
    validate_output("phase_01_encoding", p01_out)

    # Phase 02: readers
    p02_in = make_phase02_input_minimal()
    p02_in["run_id"] = run_id
    cross_field_checks(p02_in, "phase_02_readers.input")
    validate_input("phase_02_readers", p02_in)

    p02_out = make_phase02_output_ok()
    p02_out["run_id"] = run_id
    cross_field_checks(p02_out, "phase_02_readers.output")
    validate_output("phase_02_readers", p02_out)
