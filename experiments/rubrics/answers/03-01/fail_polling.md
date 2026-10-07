```python
import asyncio, time

class RateLimiter:
    def __init__(self, max_tokens, rate):
        self.max_tokens, self.rate = max_tokens, rate
        self.tokens, self.last = max_tokens, time.monotonic()

    async def acquire(self, n=1):
        while True:
            now = time.monotonic()
            self.tokens = min(self.max_tokens, self.tokens + (now - self.last) * self.rate)
            self.last = now
            if self.tokens >= n:
                self.tokens -= n
                return
            await asyncio.sleep(0.01)

async def main():
    rl = RateLimiter(5, 5)
    t = time.monotonic()
    await asyncio.gather(*(rl.acquire() for _ in range(10)))
    assert abs(time.monotonic() - t - 2.0) < 0.3

asyncio.run(main())
```
