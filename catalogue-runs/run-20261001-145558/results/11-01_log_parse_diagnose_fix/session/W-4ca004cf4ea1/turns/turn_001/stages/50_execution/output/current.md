# Revised Payment Service with Resilience Patterns
# File: app/services/payment.py

import time
import random
import threading
from typing import Optional

from app.gateways.stripe_gateway import StripeGateway
from app.exceptions import PaymentFailedException

# Simple circuit breaker implementation
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time: Optional[float] = None
        self.lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise PaymentFailedException("Circuit breaker is open; refusing request")
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            self._record_failure()
            raise
        else:
            self._reset()
            return result

    def _record_failure(self):
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

    def _reset(self):
        with self.lock:
            self.failure_count = 0
            self.state = "CLOSED"
            self.last_failure_time = None

# Exponential backoff retry decorator
def retry_with_backoff(max_retries: int = 3, base_delay: float = 0.5, backoff_factor: float = 2.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt == max_retries:
                        raise
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

class PaymentService:
    def __init__(self):
        self.gateway = StripeGateway()
        self.circuit_breaker = CircuitBreaker()
        self.idempotency_key_store = set()  # simple in‑memory store; replace with persistent store in prod

    def _generate_idempotency_key(self, order_id: str) -> str:
        # deterministic key based on order id and timestamp rounded to seconds
        return f"order-{order_id}-{int(time.time())}"

    @retry_with_backoff(max_retries=3, base_delay=0.5, backoff_factor=2.0)
    def _charge_with_resilience(self, amount: float, currency: str, idempotency_key: str):
        # Wrap the actual charge call with circuit breaker and idempotency header
        def charge():
            return self.gateway.charge(
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key,
            )
        return self.circuit_breaker.call(charge)

    def process_payment(self, order) -> str:
        """Process payment for an order.

        Args:
            order: An object with ``total``, ``currency``, and ``id`` attributes.

        Returns:
            The Stripe charge ID on success.
        """
        # Generate or retrieve idempotency key
        idempotency_key = self._generate_idempotency_key(order.id)
        if idempotency_key in self.idempotency_key_store:
            # Already processed; avoid double charge
            return "already_processed"
        # Attempt the charge with resilience patterns
        try:
            result = self._charge_with_resilience(
                amount=order.total,
                currency=order.currency,
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            raise PaymentFailedException(f"Payment failed for order {order.id}: {exc}")
        # Record successful idempotent key
        self.idempotency_key_store.add(idempotency_key)
        return result.get("id") if isinstance(result, dict) else result

# End of file
