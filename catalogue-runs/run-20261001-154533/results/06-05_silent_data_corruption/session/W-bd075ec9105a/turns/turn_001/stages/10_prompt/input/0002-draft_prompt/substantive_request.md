TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the struct packing alignment and padding issue in the provided Python code that defines functions pack_record(user_id, active, score) and unpack_record(data) using the format string 'I?d' to pack a uint32 user_id, a bool/uint8 active flag, and a float64 score. Explain why the packed size may exceed the expected 13 bytes and why the recovered values can be incorrect due to native alignment padding. Provide a corrected implementation that controls padding explicitly (e.g., using a standard size format like '<I?d' or adding explicit padding bytes) so that packing and unpacking produce the intended 13‑byte representation and accurate values.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- pack_record
- unpack_record
- struct
- I?d
- user_id
- active
- score
- uint32
- bool/uint8
- float64
