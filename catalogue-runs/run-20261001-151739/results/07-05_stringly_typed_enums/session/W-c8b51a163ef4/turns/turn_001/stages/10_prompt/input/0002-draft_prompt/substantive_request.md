TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the provided Python function process_order(order) to replace the current string‑based status checks with an enum‑based state machine. All possible order statuses and payment statuses must be represented as enums and handled exhaustively, eliminating any silent fallthroughs. The refactored code should include a test that reproduces the original bug where the 'returned' status was never handled and demonstrates that the new implementation correctly detects or handles this case.
APPROACH/RISK NOTES:
Use enum.Enum to define the OrderStatus and PaymentStatus enums, and employ exhaustive matching (e.g., full if/elif/else or a match‑case construct) to ensure every enum member is accounted for.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- process_order
- order
- 'returned'
