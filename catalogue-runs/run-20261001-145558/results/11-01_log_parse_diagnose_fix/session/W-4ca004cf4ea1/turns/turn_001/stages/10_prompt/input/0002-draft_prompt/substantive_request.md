TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Parse the provided application error log to identify the root cause and diagnose the failure. Then produce a corrected version of the payment service that adds retry with exponential backoff, a circuit breaker pattern, and an idempotency key to prevent double charges on retry. The task includes extracting relevant code locations, understanding the timeout error from the Stripe API, and implementing resilience patterns in the payment service code.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- charge
- retry
- exponential backoff
- circuit breaker
- idempotency key
