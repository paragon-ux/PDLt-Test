# Directory structure
# mypackage/
# ├── __init__.py
# ├── io.py
# ├── validation.py
# ├── transform.py
# ├── report.py
# └── tests/
#     ├── __init__.py
#     ├── test_io.py
#     ├── test_validation.py
#     ├── test_transform.py
#     └── test_report.py

# mypackage/__init__.py
"""Public interface for **mypackage**.

Exports the most commonly used functions from the sub‑modules so that users can
simply::

    import mypackage as mp
    rows = mp.read_csv('data.csv')
    errors = mp.validate_rows(rows, mp.DEFAULT_RULES)
    transformed = mp.transform_rows(rows, mp.DEFAULT_MAPPINGS)
    summary = mp.summarize(transformed, mp.DEFAULT_NUMERIC_FIELDS)
    mp.write_report(summary, 'report.json')
"""

from .io import read_csv, write_csv
from .validation import validate_row, validate_rows, DEFAULT_RULES
from .transform import transform_rows, DEFAULT_MAPPINGS
from .report import summarize, write_report, DEFAULT_NUMERIC_FIELDS

__all__ = [
    "read_csv",
    "write_csv",
    "validate_row",
    "validate_rows",
    "DEFAULT_RULES",
    "transform_rows",
    "DEFAULT_MAPPINGS",
    "summarize",
    "write_report",
    "DEFAULT_NUMERIC_FIELDS",
]

# mypackage/io.py
"""IO utilities for CSV files.

* ``read_csv(path)`` – reads a CSV file and returns a list of dictionaries.
* ``write_csv(rows, path, fieldnames=None)`` – writes an iterable of dicts to a CSV
  file.  If ``fieldnames`` is omitted the keys of the first row are used.
"""

import csv
from typing import List, Dict, Iterable, Optional

def read_csv(path: str) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of rows as dictionaries.
    
    Parameters
    ----------
    path: str
        Path to the CSV file.
    """
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(rows: Iterable[Dict[str, str]], path: str, fieldnames: Optional[List[str]] = None) -> None:
    """Write rows to a CSV file.
    
    Parameters
    ----------
    rows: iterable of dicts
        The data to write.
    path: str
        Destination file path.
    fieldnames: list of str, optional
        Column order.  If omitted the keys of the first row are used.
    """
    rows = list(rows)
    if not rows:
        raise ValueError("No rows to write")
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

# mypackage/validation.py
"""Simple data‑validation helpers.

The module defines a small rule language used by the tests:

* ``required`` – field must be present and non‑empty.
* ``numeric`` – field must contain a number (int or float).
* ``date`` – field must match ``YYYY‑MM‑DD``.
"""

import re
from datetime import datetime
from typing import Dict, List, Any

DEFAULT_RULES: Dict[str, str] = {}

def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False

def validate_row(row: Dict[str, Any], rules: Dict[str, str]) -> List[str]:
    """Validate a single row against ``rules``.
    
    Returns a list of error messages; the list is empty when the row is valid.
    """
    errors: List[str] = []
    for field, rule in rules.items():
        val = row.get(field, "")
        if rule == "required" and not val:
            errors.append(f"Missing required field: {field}")
        elif rule == "numeric" and val and not _is_numeric(val):
            errors.append(f"Field {field} is not numeric: {val}")
        elif rule == "date" and val:
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                errors.append(f"Field {field} has invalid date: {val}")
    return errors

def validate_rows(rows: List[Dict[str, Any]], rules: Dict[str, str]) -> List[Dict[str, Any]]:
    """Validate a list of rows.
    
    Returns a list of dictionaries ``{"row": row, "errors": [...]}`` for rows that
    have validation errors.
    """
    result = []
    for row in rows:
        errs = validate_row(row, rules)
        if errs:
            result.append({"row": row, "errors": errs})
    return result

# mypackage/transform.py
"""Transformation utilities.

The default mapping simply copies fields unchanged.  ``transform_rows`` takes a
mapping ``{dest: source}`` and produces a new list of dictionaries with the
requested shape.
"""

from typing import List, Dict, Any

DEFAULT_MAPPINGS: Dict[str, str] = {}

def transform_rows(rows: List[Dict[str, Any]], mappings: Dict[str, str]) -> List[Dict[str, Any]]:
    """Apply a field‑mapping transformation.
    
    ``mappings`` maps destination column names to source column names.
    """
    transformed: List[Dict[str, Any]] = []
    for row in rows:
        new_row: Dict[str, Any] = {}
        for dst, src in mappings.items():
            new_row[dst] = row.get(src, "")
        transformed.append(new_row)
    return transformed

# mypackage/report.py
"""Reporting helpers.

* ``summarize`` – compute basic statistics for numeric fields.
* ``write_report`` – dump a summary dict as pretty‑printed JSON.
"""

import json
import statistics
from typing import List, Dict, Any

DEFAULT_NUMERIC_FIELDS: List[str] = []

def summarize(rows: List[Dict[str, Any]], numeric_fields: List[str]) -> Dict[str, Dict[str, float]]:
    """Compute mean, median, stdev and count for each numeric field.
    """
    summary: Dict[str, Dict[str, float]] = {}
    for field in numeric_fields:
        values = [float(r[field]) for r in rows if r.get(field)]
        if values:
            summary[field] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "count": len(values),
            }
        else:
            summary[field] = {"mean": 0.0, "median": 0.0, "stdev": 0.0, "count": 0}
    return summary

def write_report(summary: Dict[str, Any], path: str) -> None:
    """Write the summary dictionary to ``path`` as indented JSON.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

# mypackage/tests/__init__.py
# (empty – marks the directory as a package)

# mypackage/tests/test_io.py
import os
import tempfile
import unittest
from mypackage import read_csv, write_csv

class TestIO(unittest.TestCase):
    def test_read_write_cycle(self):
        rows = [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "test.csv")
            write_csv(rows, path)
            read_back = read_csv(path)
            self.assertEqual(rows, read_back)

    def test_write_empty_raises(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "empty.csv")
            with self.assertRaises(ValueError):
                write_csv([], path)

if __name__ == "__main__":
    unittest.main()

# mypackage/tests/test_validation.py
import unittest
from mypackage import validate_row, validate_rows, DEFAULT_RULES

class TestValidation(unittest.TestCase):
    def setUp(self):
        self.rules = {"id": "required", "age": "numeric", "dob": "date"}

    def test_valid_row(self):
        row = {"id": "123", "age": "45", "dob": "2000-01-01"}
        self.assertEqual(validate_row(row, self.rules), [])

    def test_missing_required(self):
        row = {"id": "", "age": "30", "dob": "1990-05-20"}
        errors = validate_row(row, self.rules)
        self.assertIn("Missing required field: id", errors)

    def test_non_numeric(self):
        row = {"id": "1", "age": "abc", "dob": "1990-05-20"}
        errors = validate_row(row, self.rules)
        self.assertIn("Field age is not numeric: abc", errors)

    def test_invalid_date(self):
        row = {"id": "1", "age": "30", "dob": "20-05-1990"}
        errors = validate_row(row, self.rules)
        self.assertIn("Field dob has invalid date: 20-05-1990", errors)

    def test_validate_rows_aggregates(self):
        rows = [
            {"id": "1", "age": "30", "dob": "1990-01-01"},
            {"id": "", "age": "x", "dob": "bad"},
        ]
        result = validate_rows(rows, self.rules)
        self.assertEqual(len(result), 1)
        self.assertIn("Missing required field: id", result[0]["errors"][0])

if __name__ == "__main__":
    unittest.main()

# mypackage/tests/test_transform.py
import unittest
from mypackage import transform_rows, DEFAULT_MAPPINGS

class TestTransform(unittest.TestCase):
    def test_simple_mapping(self):
        rows = [{"first": "Alice", "last": "Smith"}, {"first": "Bob", "last": "Jones"}]
        mapping = {"name": "first", "surname": "last"}
        transformed = transform_rows(rows, mapping)
        expected = [{"name": "Alice", "surname": "Smith"}, {"name": "Bob", "surname": "Jones"}]
        self.assertEqual(transformed, expected)

    def test_missing_source(self):
        rows = [{"first": "Alice"}]
        mapping = {"name": "first", "surname": "last"}
        transformed = transform_rows(rows, mapping)
        self.assertEqual(transformed[0]["surname"], "")

if __name__ == "__main__":
    unittest.main()

# mypackage/tests/test_report.py
import unittest
from mypackage import summarize, write_report
import json
import os
import tempfile

class TestReport(unittest.TestCase):
    def test_summarize_statistics(self):
        rows = [{"score": "10"}, {"score": "20"}, {"score": "30"}]
        summary = summarize(rows, ["score"]) 
        self.assertAlmostEqual(summary["score"]["mean"], 20.0)
        self.assertAlmostEqual(summary["score"]["median"], 20.0)
        self.assertEqual(summary["score"]["count"], 3)

    def test_write_report_creates_file(self):
        summary = {"a": {"mean": 1, "median": 1, "stdev": 0, "count": 1}}
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "report.json")
            write_report(summary, path)
            self.assertTrue(os.path.isfile(path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(data, summary)

if __name__ == "__main__":
    unittest.main()
