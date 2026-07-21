"""Unit tests for build helper functions.

Run: python build/test_utils.py
Pure-stdlib assertions (no pytest dependency) so they run anywhere the build runs.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import clean_url, has_tracking_params, parse_semicolon, author_tag_counts


def test_clean_url_strips_tracking():
    dirty = "https://link.springer.com/article/10.1007/x?_gl=1*a&gclid=Z&foo=bar"
    assert clean_url(dirty) == "https://link.springer.com/article/10.1007/x?foo=bar"


def test_clean_url_removes_utm_prefixed():
    assert clean_url("https://x.org/a?utm_source=t&utm_medium=e&id=9") == "https://x.org/a?id=9"


def test_clean_url_drops_empty_query():
    assert clean_url("https://x.org/a?gclid=Z") == "https://x.org/a"


def test_clean_url_preserves_clean_and_nonhttp():
    assert clean_url("https://doi.org/10.1/x") == "https://doi.org/10.1/x"
    assert clean_url("") == ""
    assert clean_url("mailto:a@b.com") == "mailto:a@b.com"


def test_has_tracking_params():
    assert has_tracking_params("https://x.org/a?gclid=Z") is True
    assert has_tracking_params("https://x.org/a?utm_source=t") is True
    assert has_tracking_params("https://doi.org/10.1/x") is False


def test_parse_semicolon():
    assert parse_semicolon("a; b ;;c") == ["a", "b", "c"]
    assert parse_semicolon("") == []
    assert parse_semicolon(None) == []


def test_author_tag_counts():
    rows = [
        {"tags": "first;corresponding"},
        {"tags": "co-first"},
        {"tags": ""},
    ]
    counts = author_tag_counts(rows)
    assert counts["first"] == 1
    assert counts["corresponding"] == 1
    assert counts["co-first"] == 1
    assert counts["last"] == 0


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = []
    for test in tests:
        try:
            test()
            print(f"  ok {test.__name__}")
        except AssertionError as exc:
            failures.append((test.__name__, exc))
            print(f"  x  {test.__name__}: {exc}")
    if failures:
        print(f"\n[TESTS] FAILED: {len(failures)} of {len(tests)}")
        return 1
    print(f"\n[TESTS] PASSED: {len(tests)} unit tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
