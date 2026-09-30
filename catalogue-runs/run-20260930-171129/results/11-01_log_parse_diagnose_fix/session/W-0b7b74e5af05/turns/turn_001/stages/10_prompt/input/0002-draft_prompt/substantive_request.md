TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Parse the provided application error log to identify the root cause of payment failures, diagnose why the Stripe charge request times out, and generate a corrected version of the payment service that adds retry with exponential backoff, a circuit breaker pattern, and an idempotency key to prevent double charges on retries.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- charge
- retry
- exponential backoff
- circuit breaker
- idempotency key
