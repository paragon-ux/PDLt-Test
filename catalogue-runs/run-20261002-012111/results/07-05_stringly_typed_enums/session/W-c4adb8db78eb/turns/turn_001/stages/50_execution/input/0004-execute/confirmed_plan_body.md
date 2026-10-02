DEFINE the OrderStatus enum with members pending, confirmed, cancelled, shipped, delivered, returned
DEFINE the PaymentStatus enum with members received, failed
REFRACT the process_order function to accept OrderStatus and PaymentStatus enum types
REPLACE all order status string comparisons with exhaustive OrderStatus enum comparisons, handling each enum value explicitly and without silent fallthrough
REPLACE all payment status string comparisons with exhaustive PaymentStatus enum comparisons, handling each enum value explicitly and without silent fallthrough
ADD handling for the returned status to correctly process transition from delivered to returned
DEVELOP a unit test that creates an order with status delivered and returned flag True, invokes the refactored process_order, and verifies that the status updates to returned or raises an appropriate error
EXECUTE the unit test to confirm the bug is fixed
