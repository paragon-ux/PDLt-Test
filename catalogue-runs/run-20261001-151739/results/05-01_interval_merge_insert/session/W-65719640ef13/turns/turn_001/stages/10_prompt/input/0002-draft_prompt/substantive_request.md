TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Create a function that, given a sorted list of non-overlapping intervals and a new interval, inserts the new interval and merges any overlapping intervals, returning the resulting sorted list. The implementation must run in O(n) time. Provide unit tests covering insertion at the beginning, insertion at the end, insertion in the middle, a new interval that merges all existing intervals, a new interval that overlaps none, and an empty initial list. Example input: intervals = [[1,3], [6,9], [12,15], [18,20]], new_interval = [5,13]; expected output: [[1,3], [5,15], [18,20]].
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- intervals
- new_interval
- [[1,3], [6,9], [12,15], [18,20]]
- [5,13]
- [[1,3], [5,15], [18,20]]
