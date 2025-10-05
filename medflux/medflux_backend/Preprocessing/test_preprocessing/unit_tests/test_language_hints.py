import pytest

from medflux_backend.Preprocessing.phase_02_readers.pipeline_workflow.readers_pipeline_main import ReadersOrchestrator
from medflux_backend.Preprocessing.phase_02_readers.internal_helpers.reader_helpers_runtime_options import ReaderOptions


@pytest.fixture
def reader(tmp_path):
    return ReadersOrchestrator(tmp_path, ReaderOptions())


def test_infer_language_hint_detects_german(reader):
    assert reader._infer_language_hint('Der Vertrag und die Leistung ist valide.') == 'de'


def test_infer_language_hint_detects_english(reader):
    assert reader._infer_language_hint('The invoice date is pending for review.') == 'en'


def test_infer_language_hint_mixed(reader):
    assert reader._infer_language_hint('und the document is attached') == 'mixed'


def test_infer_locale_hint_scores_patterns(reader):
    assert reader._infer_locale_hint('Rechnungsbetrag 1.234,50 EUR am 12.10.2024') == 'de'
    assert reader._infer_locale_hint('Total 1,234.50 USD on 10/12/2024') == 'en'
    assert reader._infer_locale_hint('Amounts 1.234,50 and 1,234.50 in same doc') == 'mixed'


def test_merge_hint_prefers_specific_over_unknown(reader):
    merge = reader._merge_hint
    assert merge('unknown', 'de') == 'de'
    assert merge('de', 'de') == 'de'
    assert merge('de', 'en') == 'mixed'
    assert merge(None, 'unknown') == 'unknown'
    assert merge('unknown', 'unknown') == 'unknown'
