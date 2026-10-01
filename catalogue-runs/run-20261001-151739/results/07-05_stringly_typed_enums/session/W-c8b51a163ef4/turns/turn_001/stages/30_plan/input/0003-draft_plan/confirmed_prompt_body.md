REFRACT the Python function process_order(order) to replace string‑based status checks with an enum‑based state machine.
ENSURE that all possible order statuses and payment statuses are represented as enums and handled exhaustively, without silent fallthroughs.
INCLUDE a test that reproduces the original bug where the 'returned' status was not handled, and SHOW that the new implementation correctly detects or handles this case.
