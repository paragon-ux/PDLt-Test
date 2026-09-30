TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Perform amortized analysis of dynamic array resizing using the accounting (banker's) method. The dynamic array starts with capacity 1; when a push exceeds capacity, the array is resized to double its current capacity, copying all existing elements. Each push without resize costs 1. A resize copies all n existing elements (cost n) plus the push itself (cost 1). Assign an amortized cost per push, prove it is O(1), show the prepaid credit balance never becomes negative, and compute the exact amortized cost per operation.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- capacity 1
- push
- resize
- amortized cost
