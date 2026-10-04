`csvtool/reader.py` holds read_csv and validate_row; `csvtool/processing.py` holds transform, summarize and write_report; `csvtool/__init__.py` imports them.

```python
# csvtool/processing.py
import json, statistics
def transform(rows, mappings): ...
def summarize(rows, numeric_fields): ...
def write_report(summary, path): ...
```
Two modules are easier to navigate than five for a script this size. Tests: one test that runs the whole pipeline on a sample CSV.
