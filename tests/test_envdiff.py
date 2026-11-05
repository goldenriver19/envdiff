import tempfile
from pathlib import Path

import envdiff


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
