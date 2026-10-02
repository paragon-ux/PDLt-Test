PARSE the provided error log to determine the root cause.
IDENTIFY the root cause as a TimeoutError occurring when PaymentService's StripeGateway calls https://api.stripe.com/v1/charges (i.e., /v1/charges) and times out after 5s.
DIAGNOSE that the failure is due to missing resilience mechanisms.
GENERATE a corrected implementation of the payment service, including StripeGateway and HTTP client, that adds retry with exponential backoff, a circuit breaker pattern, and an idempotency key to prevent double charges on retries.
PRESERVE existing function names and signatures: process_payment, charge, post.
MAINTAIN the following file locations: app/services/payment.py, app/gateways/stripe_gateway.py, app/gateways/http_client.py.
USE the order identifier ORD-7842.
RESPECT the timeout duration 5s.
