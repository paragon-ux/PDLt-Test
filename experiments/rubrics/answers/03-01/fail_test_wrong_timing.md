```python
import asyncio, time

class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate = capacity, rate
        self.tokens, self.updated = capacity, time.monotonic()
        self.cond = asyncio.Condition()

    async def acquire(self, n=1):
        async with self.cond:                      # the lock keeps waiters in order
            while True:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
                self.updated = now
                if self.tokens >= n:
                    self.tokens -= n
                    return
                try:
                    await asyncio.wait_for(self.cond.wait(), (n - self.tokens) / self.rate)
                except asyncio.TimeoutError:
                    pass

async def test():
    bucket = TokenBucket(capacity=5, rate=5)       # starts full
    start = time.monotonic()
    await asyncio.gather(*(bucket.acquire() for _ in range(10)))
    assert abs(time.monotonic() - start - 2.0) <= 0.3

asyncio.run(test())
```
