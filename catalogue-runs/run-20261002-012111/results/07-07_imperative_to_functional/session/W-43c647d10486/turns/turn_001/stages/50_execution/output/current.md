def process_sales(records):
    # Step 1: Filter out refunds
    valid = [r for r in records if r['amount'] > 0 and r['status'] != 'refunded']

    # Step 2: Apply regional tax rates
    tax_rates = {'US': 0.08, 'EU': 0.20, 'UK': 0.20, 'JP': 0.10}
    taxed = [
        {**r,
         'tax_rate': tax_rates.get(r['region'], 0.15),
         'total': round(r['amount'] * (1 + tax_rates.get(r['region'], 0.15)), 2)}
        for r in valid
    ]

    # Step 3: Group by region
    groups = {}
    for r in taxed:
        groups.setdefault(r['region'], []).append(r)

    # Step 4: Compute per‑region totals
    summary = {
        region: {
            'count': len(items),
            'total': round(sum(item['total'] for item in items), 2)
        }
        for region, items in groups.items()
    }
    return summary

# Original implementation for comparison
def process_sales_original(records):
    # Step 1: Filter out refunds
    valid = []
    for r in records:
        if r['amount'] > 0 and r['status'] != 'refunded':
            valid.append(r)
    
    # Step 2: Apply regional tax rates
    taxed = []
    tax_rates = {'US': 0.08, 'EU': 0.20, 'UK': 0.20, 'JP': 0.10}
    for r in valid:
        rate = tax_rates.get(r['region'], 0.15)
        total = r['amount'] * (1 + rate)
        taxed.append({**r, 'total': round(total, 2), 'tax_rate': rate})
    
    # Step 3: Group by region
    groups = {}
    for r in taxed:
        region = r['region']
        if region not in groups:
            groups[region] = []
        groups[region].append(r)
    
    # Step 4: Compute per-region totals
    summary = {}
    for region, items in groups.items():
        total = 0
        for item in items:
            total += item['total']
        summary[region] = {'count': len(items), 'total': round(total, 2)}
    
    return summary

# Pytest‑style unit tests
def test_process_sales_functional_equivalence():
    records = [
        {'region': 'US', 'amount': 100, 'status': 'completed'},
        {'region': 'EU', 'amount': 200, 'status': 'completed'},
        {'region': 'UK', 'amount': 150, 'status': 'completed'},
        {'region': 'JP', 'amount': 120, 'status': 'completed'},
        {'region': 'CA', 'amount': 80, 'status': 'completed'},  # default rate
        {'region': 'US', 'amount': -50, 'status': 'completed'},  # negative amount filtered
        {'region': 'EU', 'amount': 100, 'status': 'refunded'},   # refunded filtered
    ]
    expected = process_sales_original(records)
    result = process_sales(records)
    assert result == expected

if __name__ == '__main__':
    test_process_sales_functional_equivalence()
    print('All tests passed.')
