DEFINE OrderStatus enum with all order status members
DEFINE PaymentStatus enum with all payment status members
REFRACT process_order to accept enum-typed order and payment status
IMPLEMENT exhaustive IF/ELIF/ELSE matching for OrderStatus covering every enum member
IMPLEMENT exhaustive IF/ELIF/ELSE matching for PaymentStatus where used
INCLUDE explicit handling for RETURNED status to avoid silent fallthrough
ADD a unit test that creates an order with status RETURNED and calls process_order
ASSERT that the test confirms the RETURNED case is detected or handled correctly
RUN the test suite to verify all branches are exercised
