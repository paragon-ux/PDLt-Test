TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose why the provided Python function serialize(Node) raises a RecursionError on deep trees, then create an iterative Python implementation of tree serialization that can handle trees of depth 100,000+ and demonstrate it on a chain of 50,000 Node instances.
APPROACH/RISK NOTES:
Implement the serialization iteratively using an explicit stack to avoid recursion depth limitations.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Node
- serialize
- depth 100,000+
