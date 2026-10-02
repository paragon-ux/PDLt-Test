TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose why the provided serialize function causes a stack overflow on deep trees, then rewrite it as an iterative solution that can serialize trees of depth at least 100,000 without recursion, and provide test code that builds a chain of 50,000 nodes to demonstrate the iterative serializer.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- serialize
- i
