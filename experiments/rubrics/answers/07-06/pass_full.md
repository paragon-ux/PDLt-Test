`mypackage/__init__.py`
```python
from .io import read_csv
from .validation import validate_row
from .transform import transform
from .report import summarize, write_report
__all__ = ["read_csv", "validate_row", "transform", "summarize", "write_report"]
```
`mypackage/io.py`
```python
import csv
def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))
```
`mypackage/validation.py`
```python
from datetime import datetime
def validate_row(row, rules):
    errors = []
    for field, rule in rules.items():
        val = row.get(field, '')
        if rule == 'required' and not val:
            errors.append(f"Missing {field}")
        elif rule == 'numeric' and val and not val.replace('.', '').isdigit():
            errors.append(f"{field} not numeric: {val}")
        elif rule == 'date':
            try: datetime.strptime(val, '%Y-%m-%d')
            except (TypeError, ValueError): errors.append(f"{field} bad date: {val}")
    return errors
```
`mypackage/transform.py`
```python
def transform(rows, mappings):
    return [{dst: row.get(src, '') for dst, src in mappings.items()} for row in rows]
```
`mypackage/report.py`
```python
import json, statistics
def summarize(rows, numeric_fields):
    summary = {}
    for field in numeric_fields:
        values = [float(r[field]) for r in rows if r.get(field)]
        summary[field] = {'mean': statistics.mean(values) if values else 0,
                          'median': statistics.median(values) if values else 0,
                          'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                          'count': len(values)}
    return summary
def write_report(summary, path):
    with open(path, 'w') as f:
        json.dump(summary, f, indent=2)
```
`tests/test_package.py`
```python
import json
from mypackage import read_csv, validate_row, transform, summarize, write_report
def test_io(tmp_path):
    p = tmp_path / "a.csv"; p.write_text("x,y\n1,2\n"); assert read_csv(p) == [{"x": "1", "y": "2"}]
def test_validation():
    assert validate_row({"a": ""}, {"a": "required"}) == ["Missing a"]
    assert validate_row({"n": "1x"}, {"n": "numeric"}) == ["n not numeric: 1x"]
    assert validate_row({"d": "2024-13-01"}, {"d": "date"}) == ["d bad date: 2024-13-01"]
def test_transform(): assert transform([{"a": 1}], {"b": "a"}) == [{"b": 1}]
def test_report(tmp_path):
    s = summarize([{"v": "1"}, {"v": "3"}], ["v"]); assert s["v"]["mean"] == 2 and s["v"]["count"] == 2
    assert summarize([], ["v"])["v"]["count"] == 0
    write_report(s, tmp_path / "r.json"); assert json.loads((tmp_path / "r.json").read_text()) == s
```
(The bare `except:` is narrowed to `(TypeError, ValueError)`: strptime raises ValueError for a malformed string and TypeError for a missing value (None from a short CSV row), so every input the original caught is still caught.)
