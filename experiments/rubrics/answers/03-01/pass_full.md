```python
import asyncio, time
from collections import deque

class TokenBucket:
    def __init__(self, capacity: float, rate: float, initial: float | None = None):
        self.capacity, self.rate = capacity, rate
        self.tokens = capacity if initial is None else initial
        self.updated = time.monotonic()
        self._waiters: deque[tuple[float, asyncio.Future]] = deque()
        self._wake: asyncio.TimerHandle | None = None

    def _refill(self):
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now

    def _serve(self):
        self._refill()
        while self._waiters and self.tokens >= self._waiters[0][0]:
            n, fut = self._waiters.popleft()
            self.tokens -= n
            if not fut.done():
                fut.set_result(None)
        if self._waiters and self._wake is None:   # one timer for the head's deficit, no polling
            delay = (self._waiters[0][0] - self.tokens) / self.rate
            self._wake = asyncio.get_running_loop().call_later(delay, self._on_timer)

    def _on_timer(self):
        self._wake = None
        self._serve()

    async def acquire(self, n: float = 1):
        if n > self.capacity:
            raise ValueError("n exceeds the bucket capacity")
        fut = asyncio.get_running_loop().create_future()
        self._waiters.append((n, fut))   # FIFO: served strictly in arrival order
        self._serve()
        await fut

async def test_ten_at_five_per_second():
    bucket = TokenBucket(capacity=5, rate=5, initial=0)   # starts empty: 10 tokens need 2 s
    start = time.monotonic()
    await asyncio.gather(*(bucket.acquire() for _ in range(10)))
    elapsed = time.monotonic() - start
    assert abs(elapsed - 2.0) <= 0.3, elapsed

asyncio.run(test_ten_at_five_per_second())
```
