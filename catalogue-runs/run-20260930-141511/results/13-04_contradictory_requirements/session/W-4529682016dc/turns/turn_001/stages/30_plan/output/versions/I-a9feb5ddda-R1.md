ANALYZE the input sequence and determine the range of key values
SELECT a linear‑time stable sorting strategy that can operate in‑place (e.g., an in‑place counting‑sort variant or an in‑place radix‑sort variant) respecting the O(1) extra‑space constraint
CONFIGURE any required counting or bucket metadata within the existing array memory without allocating additional arrays
ITERATE over the elements to compute frequency information or digit buckets as required by the chosen strategy
REARRANGE elements in‑place according to the computed frequencies or digit buckets while preserving the relative order of equal keys
VERIFY that the final ordering is stable and that no auxiliary storage beyond O(1) extra space was used
OUTPUT the sorted sequence
