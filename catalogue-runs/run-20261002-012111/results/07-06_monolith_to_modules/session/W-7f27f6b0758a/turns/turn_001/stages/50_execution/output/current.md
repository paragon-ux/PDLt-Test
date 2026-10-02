# Package: mypackage

## mypackage/__init__.py
```python
"""Top-level package for CSV processing and reporting."""

from .io import read_csv
from .validation import validate_row
from .transform import transform
from .report import summarize, write_report

__all__ = [
    "read_csv",
    "validate_row",
    "transform",
    "summarize",
    "write_report",
]
```

## mypackage/io.py
```python
"""IO utilities for reading CSV files."""

import csv
import sys
from typing import List, Dict

def read_csv(path: str) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of rows as dictionaries.

    Args:
        path: Path to the CSV file.

    Returns:
        List of rows where each row is a ``dict`` mapping column names to values.
    """
    try:
        with open(path, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        sys.stderr.write(f"Error: file not found – {path}\n")
        raise
```

## mypackage/validation.py
```python
"""Validation helpers for CSV rows."""

from datetime import datetime
from typing import Dict, List

def _is_numeric(value: str) -> bool:
    return value.replace('.', '', 1).isdigit()

def validate_row(row: Dict[str, str], rules: Dict[str, str]) -> List[str]:
    """Validate a single CSV row against supplied rules.

    Supported rules per field:
        * ``required`` – value must be present and non‑empty.
        * ``numeric`` – value must be numeric (int or float).
        * ``date`` – value must match ``YYYY‑MM‑DD``.

    Args:
        row: Mapping of column name to value.
        rules: Mapping of column name to rule name.

    Returns:
        List of error messages; empty if the row is valid.
    """
    errors: List[str] = []
    for field, rule in rules.items():
        val = row.get(field, "")
        if rule == "required" and not val:
            errors.append(f"Missing {field}")
        elif rule == "numeric" and val and not _is_numeric(val):
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
"""Transformation utilities for CSV data."""

from typing import List, Dict, Any

def transform(rows: List[Dict[str, str]], mappings: Dict[str, str]) -> List[Dict[str, str]]:
    """Transform rows according to a ``{destination: source}`` mapping.

    Args:
        rows: List of input dictionaries.
        mappings: Mapping where each key is the output field name and each value
            is the input field name to copy from.

    Returns:
        New list of rows with only the mapped fields.
    """
    result: List[Dict[str, str]] = []
    for row in rows:
        new_row: Dict[str, str] = {}
        for dst, src in mappings.items():
            new_row[dst] = row.get(src, "")
        result.append(new_row)
    return result
```

## mypackage/report.py
```python
"""Reporting utilities: summarisation and JSON output."""

import json
import statistics
from datetime import datetime
from typing import List, Dict, Any

def summarize(rows: List[Dict[str, str]], numeric_fields: List[str]) -> Dict[str, Dict[str, float]]:
    """Compute basic statistics for numeric fields.

    Returns a mapping of field name to a dictionary containing ``mean``, ``median``,
    ``stdev`` and ``count``.
    """
    summary: Dict[str, Dict[str, float]] = {}
    for field in numeric_fields:
        values = [float(r[field]) for r in rows if r.get(field)]
        summary[field] = {
            "mean": statistics.mean(values) if values else 0,
            "median": statistics.median(values) if values else 0,
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "count": len(values),
        }
    return summary

def write_report(summary: Dict[str, Any], path: str) -> None:
    """Write the summary dictionary to ``path`` as pretty‑printed JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
```

## tests/test_io.py
```python
import pathlib
import tempfile
import csv
from mypackage.io import read_csv

def test_read_csv(tmp_path: pathlib.Path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    rows = read_csv(str(csv_file))
    assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
```

## tests/test_validation.py
```python
from mypackage.validation import validate_row

def test_validate_row_required():
    row = {"name": ""}
    rules = {"name": "required"}
    assert validate_row(row, rules) == ["Missing name"]

def test_validate_row_numeric():
    row = {"age": "twenty"}
    rules = {"age": "numeric"}
    assert validate_row(row, rules) == ["age not numeric: twenty"]

def test_validate_row_date():
    row = {"dob": "2020-13-01"}
    rules = {"dob": "date"}
    assert validate_row(row, rules) == ["dob bad date: 2020-13-01"]
```

## tests/test_transform.py
```python
from mypackage.transform import transform

def test_transform_basic():
    rows = [{"src1": "a", "src2": "b"}, {"src1": "c", "src2": "d"}]
    mapping = {"dst1": "src1", "dst2": "src2"}
    expected = [{"dst1": "a", "dst2": "b"}, {"dst1": "c", "dst2": "d"}]
    assert transform(rows, mapping) == expected
```

## tests/test_report.py
```python
import pathlib
import json
from mypackage.report import summarize, write_report

def test_summarize():
    rows = [{"val": "1"}, {"val": "3"}, {"val": "5"}]
    summary = summarize(rows, ["val"])
    assert summary["val"]["mean"] == 3
    assert summary["val"]["median"] == 3
    assert summary["val"]["count"] == 3

def test_write_report(tmp_path: pathlib.Path):
    summary = {"x": {"mean": 0, "median": 0, "stdev": 0, "count": 0}}
    out_file = tmp_path / "report.json"
    write_report(summary, str(out_file))
    data = json.loads(out_file.read_text())
    assert data == summary
```
