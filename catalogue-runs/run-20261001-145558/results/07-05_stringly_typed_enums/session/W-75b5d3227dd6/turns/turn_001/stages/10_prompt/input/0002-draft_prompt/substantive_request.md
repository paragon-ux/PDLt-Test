TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the provided Python function process_order to use enum.Enum for OrderStatus and PaymentStatus, ensuring exhaustive matching for all enum values and eliminating silent fallthrough. Add a test that demonstrates the original bug where the 'returned' status was not handled and verify that the refactored version correctly handles it.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- OrderStatus
- PaymentStatus
- process_order
- 'returned'
