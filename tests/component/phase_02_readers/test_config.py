import pytest

from core.validation.registry import discover_phase, get_schema_root


pytestmark = pytest.mark.component


def test_discover_phase_paths_exist():
    paths = discover_phase("phase_02_readers", root=get_schema_root())
    assert paths["input"].exists()
    assert paths["output"].exists()
