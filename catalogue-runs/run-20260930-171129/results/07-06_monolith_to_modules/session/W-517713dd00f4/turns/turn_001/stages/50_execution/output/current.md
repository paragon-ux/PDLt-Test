# Package structure

## mypackage/__init__.py
```python
"""Top-level package for CSV processing utilities.
Exports the public API of the package.
"""

from .io import read_csv, write_csv
from .validation import validate_row
from .transform import transform
from .report import summarize, write_report

__all__ = [
    "read_csv",
    "write_csv",
    "validate_row",
    "transform",
    "summarize",
    "write_report",
]
```

## mypackage/io.py
```python
"""I/O helpers for CSV files.
Provides functions to read from and write to CSV files.
"""

import csv
from typing import List, Dict


def read_csv(path: str) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of rows as dictionaries."""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """Write a list of dictionaries to a CSV file.

    Args:
        path: Destination file path.
        rows: Iterable of row dictionaries.
        fieldnames: Column order for the output file.
    """
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
```

## mypackage/validation.py
```python
"""Validation utilities for CSV rows.
Implements basic rule‑based validation.
"""

from datetime import datetime
from typing import Dict, List


def validate_row(row: Dict[str, str], rules: Dict[str, str]) -> List[str]:
    """Validate a single CSV row against a set of rules.

    Supported rules:
        - "required": field must be present and non‑empty.
        - "numeric": field must contain a numeric value (float/int).
        - "date": field must match YYYY‑MM‑DD.
    """
    errors: List[str] = []
    for field, rule in rules.items():
        val = row.get(field, "")
        if rule == "required" and not val:
            errors.append(f"Missing {field}")
        elif rule == "numeric" and val:
            try:
                float(val)
            except ValueError:
                errors.append(f"{field} not numeric: {val}")
        elif rule == "date" and val:
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                errors.append(f"{field} bad date: {val}")
    return errors
```

## mypackage/transform.py
```python
"""Data transformation utilities.
Maps source fields to destination fields.
"""

from typing import List, Dict, Any


def transform(rows: List[Dict[str, Any]], mappings: Dict[str, str]) -> List[Dict[str, Any]]:
    """Transform rows according to a field‑mapping dictionary.

    ``mappings`` maps *destination* column names to *source* column names.
    """
    result: List[Dict[str, Any]] = []
    for row in rows:
        new: Dict[str, Any] = {}
        for dst, src in mappings.items():
            new[dst] = row.get(src, "")
        result.append(new)
    return result
```

## mypackage/report.py
```python
"""Reporting utilities.
Generates statistical summaries and writes JSON reports.
"""

import json
import statistics
from typing import List, Dict, Any


def summarize(rows: List[Dict[str, Any]], numeric_fields: List[str]) -> Dict[str, Dict[str, float]]:
    """Create a summary for each numeric field.

    Returns a mapping of field name to statistics (mean, median, stdev, count).
    """
    summary: Dict[str, Dict[str, float]] = {}
    for field in numeric_fields:
        values = [float(r[field]) for r in rows if r.get(field)]
        if not values:
            stats = {"mean": 0, "median": 0, "stdev": 0, "count": 0}
        else:
            stats = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                "count": len(values),
            }
        summary[field] = stats
    return summary


def write_report(summary: Dict[str, Any], path: str) -> None:
    """Write the summary dictionary to ``path`` as pretty‑printed JSON."""
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
```

## pyproject.toml
```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "0.1.0"
description = "A small package for CSV reading, validation, transformation, and reporting."
authors = [{name = "Generated", email = "generated@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}

[project.urls]
Homepage = "https://example.com/mypackage"
```

## tests/test_io.py
```python
import os
import tempfile
import csv
from mypackage.io import read_csv, write_csv

def test_read_write_csv():
    data = [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
    fieldnames = ["a", "b"]
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "sample.csv")
        write_csv(path, data, fieldnames)
        read_back = read_csv(path)
        assert read_back == data
```

## tests/test_validation.py
```python
import pytest
from mypackage.validation import validate_row

@pytest.mark.parametrize(
    "row,rules,expected",
    [
        ({"id": "", "age": "twenty"}, {"id": "required", "age": "numeric"}, ["Missing id", "age not numeric: twenty"]),
        ({"date": "2023-13-01"}, {"date": "date"}, ["date bad date: 2023-13-01"]),
        ({"name": "Alice"}, {"name": "required"}, []),
    ],
)
def test_validate(row, rules, expected):
    assert validate_row(row, rules) == expected
```

## tests/test_transform.py
```python
from mypackage.transform import transform

def test_transform_basic():
    rows = [{"first": "John", "last": "Doe"}, {"first": "Jane", "last": "Smith"}]
    mappings = {"full_name": "first", "surname": "last"}
    result = transform(rows, mappings)
    expected = [{"full_name": "John", "surname": "Doe"}, {"full_name": "Jane", "surname": "Smith"}]
    assert result == expected
```

## tests/test_report.py
```python
import json
import os
import tempfile
from mypackage.report import summarize, write_report

def test_summarize_and_write_report():
    rows = [{"score": "10"}, {"score": "20"}, {"score": "30"}]
    summary = summarize(rows, ["score"])
    assert summary["score"]["mean"] == 20
    assert summary["score"]["count"] == 3
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "out.json")
        write_report(summary, path)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == summary
```
