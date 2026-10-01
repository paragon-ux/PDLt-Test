import asyncio
import time
from collections import deque

class AsyncTokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self._tokens = capacity
        self._lock = asyncio.Condition()
        self._queue = deque()
        self._last_refill = time.monotonic()
        self._refill_task = asyncio.create_task(self._refill_loop())
        self._closed = False

    async def _refill_loop(self):
        try:
            while not self._closed:
                async with self._lock:
                    now = time.monotonic()
                    elapsed = now - self._last_refill
                    added = elapsed * self.refill_rate
                    if added >= 1:
                        self._tokens = min(self.capacity, self._tokens + int(added))
                        self._last_refill = now
                        self._lock.notify_all()
                await asyncio.sleep(0.01)  # small sleep to avoid busy‑wait
        except asyncio.CancelledError:
            pass

    async def acquire(self, n: int = 1):
        future = asyncio.get_running_loop().create_future()
        async with self._lock:
            self._queue.append((n, future))
            while True:
                # Check if this request is at the front and enough tokens exist
                if self._queue[0][1] is future and self._tokens >= n:
                    self._tokens -= n
                    self._queue.popleft()
                    future.set_result(True)
                    self._lock.notify_all()
                    return
                await self._lock.wait()

    async def close(self):
        self._closed = True
        self._refill_task.cancel()
        try:
            await self._refill_task
        except asyncio.CancelledError:
            pass

# Test
async def _test():
    limiter = AsyncTokenBucket(capacity=5, refill_rate=5)  # 5 tokens/sec, burst up to 5
    async def worker(i):
        await limiter.acquire(1)
        return i
    start = time.monotonic()
    results = await asyncio.gather(*(worker(i) for i in range(10)))
    elapsed = time.monotonic() - start
    await limiter.close()
    assert abs(elapsed - 2.0) <= 0.3, f"Elapsed time {elapsed:.2f}s not within tolerance"
    print(f"Test passed, elapsed: {elapsed:.2f}s")

if __name__ == "__main__":
    asyncio.run(_test())
