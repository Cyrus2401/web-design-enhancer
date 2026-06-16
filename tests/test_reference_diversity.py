"""
tests/test_reference_diversity.py
Anti-monoculture check for Phase 0 references (recommendation #2).

getdesign's catalogue is ~70% SaaS/tech. Anchoring only on SaaS brands
reproduces the "every AI site looks like a San-Francisco SaaS" failure.
check.py classifies references via data/getdesign-references.csv and WARNS
(never blocks) when every reference is SaaS/tech. These tests exercise the
normalization, CSV loading, and classification logic directly.
"""
import importlib.util
from pathlib import Path

_CHECK = Path(__file__).parent.parent / "scripts" / "check.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_mod_div", _CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _F:
    """Minimal stand-in for a Path with a .name attribute."""
    def __init__(self, name):
        self.name = name


# --- normalization ---------------------------------------------------------

def test_normalize_strips_getdesign_prefix_and_md():
    c = _load()
    assert c._normalize_brand("getdesign-linear.md") == "linear"
    assert c._normalize_brand("brand-nike.md") == "nike"


def test_normalize_strips_tld_suffixes():
    c = _load()
    assert c._normalize_brand("linear.app") == "linear"
    assert c._normalize_brand("mistral.ai") == "mistral"


def test_normalize_preserves_internal_hyphens():
    c = _load()
    assert c._normalize_brand("getdesign-nintendo-2001.md") == "nintendo-2001"
    assert c._normalize_brand("bmw-m") == "bmw-m"


def test_normalize_filename_matches_catalogue_id():
    # The file written for `add linear.app` is getdesign-linear.md — both
    # must normalize to the same key so the CSV lookup succeeds.
    c = _load()
    assert c._normalize_brand("getdesign-linear.md") == c._normalize_brand("linear.app")


# --- CSV loading -----------------------------------------------------------

def test_csv_loads_known_segments():
    c = _load()
    segs = c._load_reference_segments()
    assert segs.get("linear") == "saas"
    assert segs.get("stripe") == "saas"
    assert segs.get("wired") == "non-saas"
    assert segs.get("nike") == "non-saas"
    assert segs.get("nintendo-2001") == "non-saas"


def test_csv_has_both_segments():
    c = _load()
    segs = c._load_reference_segments()
    assert "saas" in segs.values()
    assert "non-saas" in segs.values()


# --- classification --------------------------------------------------------

def test_all_saas_emits_monoculture_warning():
    c = _load()
    w = c._check_reference_diversity([_F("getdesign-stripe.md"),
                                      _F("getdesign-vercel.md")])
    assert len(w) == 1
    assert "monoculture" in w[0]


def test_non_saas_present_no_warning():
    c = _load()
    w = c._check_reference_diversity([_F("getdesign-stripe.md"),
                                      _F("getdesign-nike.md")])
    assert w == []


def test_unknown_brand_never_blocks():
    c = _load()
    w = c._check_reference_diversity([_F("getdesign-foobar.md")])
    assert w == []


def test_diversity_check_returns_only_warnings_never_errors():
    # The check is a nudge: it must never contribute to gate 0 errors.
    c = _load()
    for files in ([_F("getdesign-stripe.md")],
                  [_F("getdesign-wired.md")],
                  [_F("getdesign-unknownbrand.md")]):
        result = c._check_reference_diversity(files)
        assert isinstance(result, list)
