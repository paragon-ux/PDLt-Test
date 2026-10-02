# File: app/gateways/http_client.py
import time
import random
import requests
from typing import Any, Dict

class HttpClient:
    def __init__(self, base_url: str, timeout: int = 5, max_retries: int = 3, backoff_factor: float = 0.5):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()

    def _request_with_retry(self, method: str, path: str, **kwargs) -> requests.Response:
        """Perform an HTTP request with exponential backoff retry.
        Retries are only attempted for timeout errors and 5xx responses.
        """
        url = f"{self.base_url}{path}"
        attempt = 0
        while True:
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                # Retry on server errors (5xx)
                if 500 <= response.status_code < 600:
                    raise requests.HTTPError(f"Server error: {response.status_code}")
                return response
            except (requests.Timeout, requests.HTTPError) as exc:
                attempt += 1
                if attempt > self.max_retries:
                    raise TimeoutError(f"Request to {url} timed out after {self.timeout}s (retries exhausted)") from exc
                # exponential backoff with jitter
                backoff = self.backoff_factor * (2 ** (attempt - 1))
                jitter = random.uniform(0, backoff)
                time.sleep(backoff + jitter)

    def post(self, path: str, json: Dict[str, Any] = None, **kwargs) -> Any:
        return self._request_with_retry('POST', path, json=json, **kwargs).json()

    def get(self, path: str, params: Dict[str, Any] = None, **kwargs) -> Any:
        return self._request_with_retry('GET', path, params=params, **kwargs).json()

# File: app/gateways/stripe_gateway.py
import uuid
from typing import Any, Dict
from .http_client import HttpClient

class CircuitBreakerOpen(Exception):
    pass

class StripeGateway:
    def __init__(self, client: HttpClient, circuit_breaker_threshold: int = 5, circuit_breaker_timeout: int = 30):
        self._client = client
        self.base_url = "https://api.stripe.com"
        self._failure_count = 0
        self._circuit_breaker_threshold = circuit_breaker_threshold
        self._circuit_breaker_timeout = circuit_breaker_timeout
        self._circuit_opened_at = None

    def _circuit_open(self) -> bool:
        if self._failure_count >= self._circuit_breaker_threshold:
            if self._circuit_opened_at is None:
                self._circuit_opened_at = time.time()
            elif time.time() - self._circuit_opened_at < self._circuit_breaker_timeout:
                return True
            else:
                # reset circuit
                self._failure_count = 0
                self._circuit_opened_at = None
        return False

    def post(self, path: str, data: Dict[str, Any]):
        if self._circuit_open():
            raise CircuitBreakerOpen("Circuit breaker is open; request blocked.")
        try:
            response = self._client.post(path, json=data)
            # successful request, reset failure count
            self._failure_count = 0
            self._circuit_opened_at = None
            return response
        except Exception as exc:
            self._failure_count += 1
            raise

    def charge(self, amount: int, currency: str, order_id: str) -> Dict[str, Any]:
        # idempotency key based on order identifier
        idempotency_key = f"order-{order_id}"  # using ORD-7842
        payload = {
            "amount": amount,
            "currency": currency,
            "metadata": {"order_id": order_id},
        }
        headers = {"Idempotency-Key": idempotency_key}
        # Pass headers via client (requests allows custom headers)
        return self._client._request_with_retry('POST', f"/v1/charges", json=payload, headers=headers)

# File: app/services/payment.py
from .gateways.stripe_gateway import StripeGateway
from .gateways.http_client import HttpClient

class PaymentService:
    def __init__(self):
        http_client = HttpClient(base_url="https://api.stripe.com", timeout=5)
        self.gateway = StripeGateway(client=http_client)

    def process_payment(self, order) -> Any:
        # Preserve original signature
        amount = order.total
        currency = order.currency
        order_id = getattr(order, 'id', 'unknown')
        return self.gateway.charge(amount=amount, currency=currency, order_id=order_id)
