import asyncio
import time

class AsyncTokenBucket:
    """Asynchronous token bucket rate limiter.

    Args:
        capacity: Maximum number of tokens (burst capacity).
        refill_rate: Tokens added per second.
    """
    def __init__(self, capacity: int, refill_rate: float):
        self._capacity = capacity
        self._tokens = capacity
        self._refill_rate = refill_rate
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition()
        self._last_refill = time.monotonic()
        self._refill_task = asyncio.create_task(self._refill_loop())

    async def _refill_loop(self):
        """Periodically refill tokens based on elapsed time."""
        while True:
            async with self._condition:
                now = time.monotonic()
                elapsed = now - self._last_refill
                added = elapsed * self._refill_rate
                if added >= 1:
                    self._tokens = min(self._capacity, self._tokens + int(added))
                    self._last_refill = now
                    self._condition.notify_all()
            await asyncio.sleep(0.01)  # small sleep to avoid busy‑wait

    async def acquire(self, n: int = 1):
        """Acquire *n* tokens, waiting if necessary.

        Calls are served in FIFO order because each waiter obtains the
        condition lock sequentially.
        """
        async with self._condition:
            while self._tokens < n:
                await self._condition.wait()
            self._tokens -= n

    async def close(self):
        """Cancel the refill background task."""
        self._refill_task.cancel()
        try:
            await self._refill_task
        except asyncio.CancelledError:
            pass

# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------
async def _worker(bucket: AsyncTokenBucket, idx: int):
    await bucket.acquire(1)
    # For demonstration, record acquisition time
    print(f"Task {idx} acquired token at {time.monotonic():.4f}")

async def main():
    rate = 5  # tokens per second
    capacity = 5
    bucket = AsyncTokenBucket(capacity=capacity, refill_rate=rate)
    start = time.monotonic()
    tasks = [asyncio.create_task(_worker(bucket, i)) for i in range(10)]
    await asyncio.gather(*tasks)
    end = time.monotonic()
    elapsed = end - start
    print(f"Elapsed: {elapsed:.3f} seconds")
    # Verify elapsed time approx 2 seconds +/- 0.3
    assert abs(elapsed - 2.0) <= 0.3, "Timing verification failed"
    await bucket.close()

if __name__ == "__main__":
    asyncio.run(main())
