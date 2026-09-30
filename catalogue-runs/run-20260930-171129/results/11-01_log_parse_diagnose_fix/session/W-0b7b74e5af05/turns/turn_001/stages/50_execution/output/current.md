# payment_service.py
import time
import random
import threading
from typing import Any, Dict

class CircuitBreakerState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fail_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = None
        self.lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise RuntimeError("Circuit breaker is open")
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            self._record_failure()
            raise
        else:
            self._reset()
            return result

    def _record_failure(self):
        with self.lock:
            self.fail_count += 1
            self.last_failure_time = time.time()
            if self.fail_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN

    def _reset(self):
        with self.lock:
            self.fail_count = 0
            self.state = CircuitBreakerState.CLOSED

class StripeGateway:
    def __init__(self, client, base_url="https://api.stripe.com", timeout: int = 5):
        self._client = client
        self.base_url = base_url
        self.timeout = timeout
        self.circuit_breaker = CircuitBreaker()
        self.idempotency_key_generator = lambda: str(random.getrandbits(128))

    def charge(self, amount: int, currency: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "amount": amount,
            "currency": currency,
            "idempotency_key": kwargs.get("idempotency_key", self.idempotency_key_generator()),
        }
        # Wrap the HTTP call with circuit breaker and retry logic
        return self._execute_with_retry(lambda: self.circuit_breaker.call(self._post, "/v1/charges", payload))

    def _post(self, path: str, data: Dict[str, Any]):
        return self._client.post(self.base_url + path, json=data, timeout=self.timeout)

    def _execute_with_retry(self, func, max_retries: int = 3, base_delay: float = 0.5):
        attempt = 0
        while True:
            try:
                return func()
            except Exception as exc:
                attempt += 1
                if attempt > max_retries:
                    raise
                # exponential backoff with jitter
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
                time.sleep(delay)

class PaymentService:
    def __init__(self, gateway: StripeGateway):
        self.gateway = gateway

    def process_payment(self, order) -> str:
        """Process payment for an order.
        Returns the Stripe charge ID on success.
        """
        idempotency_key = f"order-{order.id}"  # deterministic per order
        result = self.gateway.charge(
            amount=order.total,
            currency=order.currency,
            idempotency_key=idempotency_key,
        )
        return result.get("id")
