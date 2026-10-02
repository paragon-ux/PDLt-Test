DEFINE the OrderStatus enum with members: pending, confirmed, cancelled, shipped, delivered, returned
DEFINE the PaymentStatus enum with members: received, failed
REFRACTOR the process_order function to use enum.Enum types for order status and payment status
REPLACE all string comparisons on order['status'] with exhaustive enum comparisons, handling each OrderStatus value explicitly and ensuring no silent fallthrough
REPLACE all string comparisons on order['payment'] with exhaustive enum comparisons, handling each PaymentStatus value explicitly and ensuring no silent fallthrough
ADD handling for the returned status to correctly process transition from delivered to returned
PROVIDE a unit test that reproduces the original bug where an order has status delivered and returned is True, and verifies that the refactored code correctly updates the status or raises an appropriate error, confirming the bug is fixed
