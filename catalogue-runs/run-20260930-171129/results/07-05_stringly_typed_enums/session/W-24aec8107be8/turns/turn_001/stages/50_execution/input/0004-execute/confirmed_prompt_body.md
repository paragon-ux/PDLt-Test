REFRACT the provided Python `process_order` function to use `enum.Enum` for `OrderStatus` and `PaymentStatus`.
DEFINE the `OrderStatus` enum with all possible status values, including `returned`.
DEFINE the `PaymentStatus` enum with all possible payment states.
UPDATE `process_order` to perform exhaustive matching on each `OrderStatus` and `PaymentStatus` value, ensuring no silent fallthrough occurs.
ADD a unit test that creates an `order` with status `returned` to reproduce the original bug scenario and asserts that the refactored implementation detects or handles the missing case appropriately.
