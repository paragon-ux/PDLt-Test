DEFINE the function process_sales(records)
  FILTER records to retain only those where amount > 0 AND status != refunded
  MAP each filtered record to assign a rate based on region using the mapping US:0.08, EU:0.20, UK:0.20, JP:0.10, default:0.15
  MAP each record to compute total = amount * (1 + rate) and round the result to 2 decimal places
  GROUP the mapped records by region into groups
  REDUCE each group to produce a summary containing count of items and sum of total, rounding the sum to 2 decimal places
  RETURN a summary dictionary mapping each region to its summary
PROVIDE pytest‑style unit tests
  CREATE a sample dataset that includes at least one record for each region and includes a refunded record
  CALL the original process_sales implementation with the sample dataset
  CALL the functional process_sales implementation with the same dataset
  ASSERT that the summary output from both calls is identical
