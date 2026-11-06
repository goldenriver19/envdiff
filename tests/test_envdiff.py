import tempfile
from pathlib import Path

import envdiff
import pytest


def write_env(content):
    handle = tempfile.NamedTemporaryFile("w", delete=False, suffix=".env")
    handle.write(content)
    handle.close()
    return handle.name


def test_compare_reports_differences():
    left = write_env("A=1\nB=2\nC=3\n")
    right = write_env("A=1\nB=9\nD=4\n")
    result = envdiff.compare(envdiff.parse_env(left), envdiff.parse_env(right))
    assert result == {"missing": ["C"], "extra": ["D"], "changed": ["B"]}


def test_ignore_keys():
    left = write_env("A=1\nB=2\n")
    right = write_env("A=1\n")
    result = envdiff.compare(envdiff.parse_env(left), envdiff.parse_env(right), ["B"])
    assert result == {"missing": [], "extra": [], "changed": []}


def test_export_and_inline_comments():
    left = write_env('export A=1 # first\nB="two words"\n')
    right = write_env("A=1\nB=two words # trailing\n")
    assert envdiff.parse_env(left) == {"A": "1", "B": "two words"}
    assert envdiff.parse_env(right) == {"A": "1", "B": "two words"}


def test_quoted_values_preserve_inline_hashes(tmp_path):
    path = tmp_path / "quoted.env"
    path.write_text(
        'A="secret # value" # trailing\n'
        "B='x # y' # trailing\n"
        'C="line\\nbreak"\n'
    )
    assert envdiff.parse_env(str(path)) == {
        "A": "secret # value",
        "B": "x # y",
        "C": "line\nbreak",
    }


def test_unquoted_values_keep_hashes_without_whitespace(tmp_path):
    path = tmp_path / "unquoted.env"
    path.write_text("URL=https://example.com/#fragment\nTAG=v1.2.3#build\n")
    assert envdiff.parse_env(str(path)) == {
        "URL": "https://example.com/#fragment",
        "TAG": "v1.2.3#build",
    }


def test_export_prefix_with_extra_whitespace(tmp_path):
    path = tmp_path / "export.env"
    path.write_text("export   A=1\nexport\tB=2\n")
    assert envdiff.parse_env(str(path)) == {"A": "1", "B": "2"}


def test_parse_env_rejects_invalid_lines(tmp_path):
    path = tmp_path / "invalid.env"
    path.write_text("NOT_A_VALID_LINE\n")
    with pytest.raises(ValueError, match="invalid line"):
        envdiff.parse_env(str(path))


def test_parse_env_rejects_empty_key(tmp_path):
    path = tmp_path / "empty.env"
    path.write_text("=value\n")
    with pytest.raises(ValueError, match="empty key"):
        envdiff.parse_env(str(path))


def test_main_reports_missing_file(tmp_path):
    missing = tmp_path / "does-not-exist.env"
    assert envdiff.main([str(missing), str(missing)]) == 2


def test_main_accepts_repeated_ignore_options(tmp_path):
    left = tmp_path / "left.env"
    right = tmp_path / "right.env"
    left.write_text("A=1\nB=2\nC=3\n")
    right.write_text("A=1\n")
    assert envdiff.main([str(left), str(right), "--ignore", "B", "--ignore", "C"]) == 0
