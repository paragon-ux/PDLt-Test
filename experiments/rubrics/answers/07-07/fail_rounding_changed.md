```python
from itertools import groupby

def process_sales(records):
    rates = {'US': 0.08, 'EU': 0.20, 'UK': 0.20, 'JP': 0.10}
    valid = [r for r in records if r['amount'] > 0 and r['status'] != 'refunded']
    taxed = [{**r, 'total': r['amount'] * (1 + rates.get(r['region'], 0.15)), 'tax_rate': rates.get(r['region'], 0.15)}
             for r in valid]
    key = lambda r: r['region']
    return {region: {'count': len(items), 'total': round(sum(i['total'] for i in items), 2)}
            for region, items in ((k, list(g)) for k, g in groupby(sorted(taxed, key=key), key=key))}
```
Test: on a small sample of US and EU records the summary matches the expected counts.
