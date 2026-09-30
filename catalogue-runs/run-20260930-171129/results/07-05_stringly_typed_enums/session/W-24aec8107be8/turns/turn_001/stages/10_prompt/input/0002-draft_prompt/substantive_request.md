TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the provided Python `process_order` function to use `enum.Enum` for `OrderStatus` and `PaymentStatus`. Ensure every enum value is explicitly handled with exhaustive matching so no silent fallthrough occurs (e.g., the 'returned' status bug). Include a test that reproduces the original bug scenario and verifies that the refactored implementation detects or handles the missing case.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- process_order
- OrderStatus
- PaymentStatus
- enum.Enum
- order
- status
- returned
