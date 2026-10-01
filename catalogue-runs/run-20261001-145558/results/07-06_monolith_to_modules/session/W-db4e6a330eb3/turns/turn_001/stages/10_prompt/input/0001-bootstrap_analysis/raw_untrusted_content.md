The following single-file script handles CSV processing, validation, transformation, and reporting. Split it into a proper multi-module Python package with clear imports.

`python
import csv, sys, json, statistics
from datetime import datetime

def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))

def validate_row(row, rules):
    errors = []
    for field, rule in rules.items():
        val = row.get(field, '')
        if rule == 'required' and not val:
            errors.append(f"Missing {field}")
        elif rule == 'numeric' and val and not val.replace('.','').isdigit():
            errors.append(f"{field} not numeric: {val}")
        elif rule == 'date':
            try: datetime.strptime(val, '%Y-%m-%d')
            except: errors.append(f"{field} bad date: {val}")
    return errors

def transform(rows, mappings):
    result = []
    for row in rows:
        new = {}
        for dst, src in mappings.items():
            new[dst] = row.get(src, '')
        result.append(new)
    return result

def summarize(rows, numeric_fields):
    summary = {}
    for field in numeric_fields:
        values = [float(r[field]) for r in rows if r.get(field)]
        summary[field] = {
            'mean': statistics.mean(values) if values else 0,
            'median': statistics.median(values) if values else 0,
            'stdev': statistics.stdev(values) if len(values) > 1 else 0,
            'count': len(values)
        }
    return summary

def write_report(summary, path):
    with open(path, 'w') as f:
        json.dump(summary, f, indent=2)
`

Organize as: mypackage/__init__.py, mypackage/io.py, mypackage/validation.py, mypackage/transform.py, mypackage/report.py. Include tests for each module.
