READ the provided application error log to locate the TimeoutError occurring when calling the Stripe API
IDENTIFY the root cause of the TimeoutError in the context of the PaymentService execution
DIAGNOSE why the failure propagates to the payment processing flow
CREATE a corrected version of the payment service implementation that:
MODIFIES the PaymentService class and related gateway code
PRESERVES the existing interfaces process_payment and charge
IMPLEMENTS retry logic with exponential backoff for Stripe API calls
INTEGRATES a circuit breaker pattern to halt retries after repeated failures
USES an idempotency key to prevent double charges on retry attempts
RETAINS handling of order failures as in the original behavior
OUTPUT the revised code snippets for PaymentService, the gateway handling, and any supporting components required for the retry, circuit breaker, and idempotency mechanisms
