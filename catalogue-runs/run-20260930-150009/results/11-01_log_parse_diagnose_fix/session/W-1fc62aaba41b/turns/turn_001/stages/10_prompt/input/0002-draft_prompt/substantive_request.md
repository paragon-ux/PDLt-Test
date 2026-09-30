TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Parse the provided application error log to identify the root cause (TimeoutError when calling Stripe API), diagnose the failure, and produce a corrected version of the payment service that implements retry with exponential backoff, a circuit breaker pattern, and uses an idempotency key to prevent double charges on retry. The fix must modify the PaymentService and related gateway code, preserving existing interfaces such as process_payment and charge, and retain handling of order failures.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- PaymentService
- process_payment
- charge
- TimeoutError
