REFactor the function process_order to use enum.Enum for OrderStatus and PaymentStatus.
ENSURE exhaustive matching for all enum values, eliminating any silent fallthrough.
ADD a test that demonstrates the original bug where the 'returned' status was not handled.
VERIFY that the refactored version correctly handles the 'returned' status.
