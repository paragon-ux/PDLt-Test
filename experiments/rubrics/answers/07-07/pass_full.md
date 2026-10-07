```python
from functools import reduce

TAX_RATES = {'US': 0.08, 'EU': 0.20, 'UK': 0.20, 'JP': 0.10}

def process_sales_functional(records):
    valid = filter(lambda r: r['amount'] > 0 and r['status'] != 'refunded', records)
    taxed = [{**r, 'total': round(r['amount'] * (1 + TAX_RATES.get(r['region'], 0.15)), 2),
              'tax_rate': TAX_RATES.get(r['region'], 0.15)} for r in valid]
    groups = reduce(lambda acc, r: {**acc, r['region']: acc.get(r['region'], []) + [r]}, taxed, {})
    return {region: {'count': len(items), 'total': round(reduce(lambda s, i: s + i['total'], items, 0), 2)}
            for region, items in groups.items()}
```
Test:
```python
SAMPLE = [
    {'amount': 100.0, 'status': 'ok', 'region': 'US'}, {'amount': 19.99, 'status': 'ok', 'region': 'EU'},
    {'amount': 50.0, 'status': 'refunded', 'region': 'US'}, {'amount': 0, 'status': 'ok', 'region': 'JP'},
    {'amount': -5, 'status': 'ok', 'region': 'UK'}, {'amount': 33.33, 'status': 'ok', 'region': 'BR'},
    {'amount': 12.5, 'status': 'ok', 'region': 'US'}, {'amount': 7.77, 'status': 'ok', 'region': 'JP'},
]
def test_identical_output():
    assert process_sales_functional(SAMPLE) == process_sales(SAMPLE)   # process_sales: the original, unchanged
    assert list(process_sales_functional(SAMPLE)) == list(process_sales(SAMPLE))   # same region order
```
