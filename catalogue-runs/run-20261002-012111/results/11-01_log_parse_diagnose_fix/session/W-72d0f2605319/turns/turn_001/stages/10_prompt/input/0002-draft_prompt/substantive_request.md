TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Parse the provided error log to determine the root cause (a TimeoutError when the PaymentService's StripeGateway calls https://api.stripe.com/v1/charges and times out after 5s), diagnose that the failure is due to missing resilience mechanisms, and generate a corrected implementation of the payment service (including the StripeGateway and HTTP client) that adds retry with exponential backoff, a circuit breaker pattern, and an idempotency key to prevent double charges on retries. Preserve existing function names and signatures such as process_payment, charge, post, and maintain file locations app/services/payment.py, app/gateways/stripe_gateway.py, app/gateways/http_client.py. Use the order identifier ORD-7842 and respect the timeout duration 5s.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- app/services/payment.py
- app/gateways/stripe_gateway.py
- app/gateways/http_client.py
- process_payment
- charge
- post
- TimeoutError
- https://api.stripe.com/v1/charges
- /v1/charges
- ORD-7842
- 5s
- PaymentService
- order
- exponential backoff
- circuit breaker pattern
- idempotency key
