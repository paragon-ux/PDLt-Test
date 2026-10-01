READ the existing process_order function source code
DEFINE OrderStatus enum with all possible order statuses
DEFINE PaymentStatus enum with all possible payment statuses
UPDATE process_order to accept enum values instead of raw strings
IMPLEMENT exhaustive matching for each enum value using CASE/ENDCASE structures, ensuring no silent fallthrough
WRITE a unit test that sets the order status to 'returned' and confirms the original bug manifested
UPDATE or add a unit test that verifies the refactored process_order correctly handles the 'returned' status
EXECUTE the test suite to confirm the refactored code passes all tests
