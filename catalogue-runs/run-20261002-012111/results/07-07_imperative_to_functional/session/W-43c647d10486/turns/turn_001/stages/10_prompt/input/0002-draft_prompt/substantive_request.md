TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Rewrite the provided Python function `process_sales` that takes a list of record dictionaries and performs four steps: filter out refunds (records where `amount` > 0 and `status` != `refunded`), apply regional tax rates using the mapping {'US': 0.08, 'EU': 0.20, 'UK': 0.20, 'JP': 0.10} and a default rate of 0.15, group the resulting records by their `region` field, and compute per‑region summary statistics (count of items and total of the `total` field, rounded to two decimals). The functional version must use map, filter, reduce, and comprehensions while preserving the exact output dictionary returned by the original function. Additionally, provide unit tests with a sample dataset that demonstrate the functional implementation yields identical results.
APPROACH/RISK NOTES:
Rewrite the imperative loops using Python's functional constructs. Use `filter` (or a list comprehension) to keep records with a positive `amount` and a `status` not equal to `refunded`. Use `map` (or a comprehension) to add `total` and `tax_rate` fields based on `tax_rates` with a fallback of 0.15, rounding the total to two decimals. Group the mapped records by `region` using a dictionary comprehension or `itertools.groupby`. Compute per‑region aggregates with `reduce` or a comprehension that sums `total` values and counts items, rounding the final total. Supply pytest‑style tests that create a representative dataset, run both the original and functional implementations, and assert the returned summary dictionaries are equal.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- process_sales
- records
- r
- amount
- status
- refunded
- US
- EU
- UK
- JP
- region
- rate
- total
- summary
- items
- item
- count
- round
- 0
- 0.08
- 0.20
- 0.10
- 0.15
- 2
- map
- filter
- reduce
- comprehensions
