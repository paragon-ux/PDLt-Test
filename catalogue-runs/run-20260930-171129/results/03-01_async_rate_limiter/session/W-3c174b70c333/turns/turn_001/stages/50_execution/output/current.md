import asyncio
import time
from collections import deque

class TokenBucket:
    """Async token bucket rate limiter with FIFO fairness.
    
    Args:
        max_tokens: maximum burst capacity (tokens).
        refill_rate: tokens added per second (float).
    """
    def __init__(self, max_tokens: int, refill_rate: float):
        self._max_tokens = max_tokens
        self._tokens = max_tokens
        self._refill_rate = refill_rate
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._waiters = deque()  # each entry is (n, future)
        self._last_refill = time.monotonic()
        # start background refill task
        self._refill_task = asyncio.create_task(self._refill_loop())

    async def _refill_loop(self):
        while True:
            await asyncio.sleep(0.01)
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._last_refill = now
                added = elapsed * self._refill_rate
                if added:
                    self._tokens = min(self._max_tokens, self._tokens + added)
                # wake waiting coroutines if possible
                while self._waiters:
                    n, fut = self._waiters[0]
                    if self._tokens >= n:
                        self._tokens -= n
                        self._waiters.popleft()
                        if not fut.done():
                            fut.set_result(True)
                    else:
                        break
                self._condition.notify_all()

    async def acquire(self, n: int = 1):
        """Acquire *n* tokens, waiting FIFO until enough are available."""
        if n <= 0:
            raise ValueError("n must be positive")
        async with self._lock:
            # fast path
            if self._tokens >= n and not self._waiters:
                self._tokens -= n
                return
            # otherwise enqueue and wait
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            self._waiters.append((n, fut))
            # wait until future is set by refill loop
            await fut

    def close(self):
        self._refill_task.cancel()

# Test for the token bucket
async def _worker(name: str, bucket: TokenBucket):
    await bucket.acquire(1)
    # simulate work
    return name

async def main_test():
    bucket = TokenBucket(max_tokens=5, refill_rate=5)  # 5 tokens per second, burst 5
    start = time.monotonic()
    tasks = [asyncio.create_task(_worker(f"task-{i}", bucket)) for i in range(10)]
    results = await asyncio.ggather(*tasks)
    elapsed = time.monotonic() - start
    print("Elapsed:", elapsed)
    # Verify roughly 2 seconds (+/-0.3)
    assert 1.7 <= elapsed <= 2.3, f"Elapsed time {elapsed:.2f}s out of expected range"
    bucket.close()
    print("All tasks completed:", results)

if __name__ == "__main__":
    asyncio.run(main_test())
