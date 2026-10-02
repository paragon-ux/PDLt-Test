PARSE the provided error log to extract failure events
IDENTIFY the root cause as a TimeoutError occurring when StripeGateway calls https://api.stripe.com/v1/charges
DIAGNOSE that the failure is due to missing resilience mechanisms
DESIGN a corrected implementation of the payment service that adds:
    ADD a retry mechanism with exponential backoff to the HTTP client
    ADD a circuit breaker pattern to the StripeGateway
    ADD generation of an idempotency key using the order identifier ORD-7842 to prevent double charges on retries
ENSURE existing function names and signatures (process_payment, charge, post) are preserved
UPDATE app/services/payment.py to integrate the resilient StripeGateway
UPDATE app/gateways/stripe_gateway.py with circuit breaker and idempotency logic
UPDATE app/gateways/http_client.py with retry and exponential backoff logic
CONFIGURE all requests to respect a 5‑second timeout
VERIFY that the implementation conforms to the specified file locations and constraints
