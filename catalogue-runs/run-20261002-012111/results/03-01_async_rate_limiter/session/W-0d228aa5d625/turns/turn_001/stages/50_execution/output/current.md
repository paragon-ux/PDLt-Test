import asyncio
import time

class AsyncTokenBucket:
    """Asynchronous token bucket rate limiter.

    Parameters
    ----------
    capacity: int
        Maximum number of tokens (burst capacity).
    refill_rate: float
        Tokens added per second.
    """
    def __init__(self, capacity: int, refill_rate: float):
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = capacity
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition()
        self._queue = []  # FIFO list of pending (n, future)
        self._replenisher_task = asyncio.create_task(self._replenish())
        self._closed = False

    async def _replenish(self):
        interval = 1.0 / self._refill_rate if self._refill_rate != 0 else float('inf')
        while not self._closed:
            await asyncio.sleep(interval)
            async with self._lock:
                if self._tokens < self._capacity:
                    self._tokens = min(self._capacity, self._tokens + 1)
                # Notify waiting tasks that tokens may be available
                async with self._condition:
                    self._condition.notify_all()
                # Try to satisfy queued requests in order
                await self._process_queue()

    async def _process_queue(self):
        async with self._condition:
            while self._queue:
                n, fut = self._queue[0]
                if self._tokens >= n:
                    self._tokens -= n
                    self._queue.pop(0)
                    if not fut.done():
                        fut.set_result(True)
                else:
                    break

    async def acquire(self, n: int = 1):
        if n <= 0:
            raise ValueError("Requested token count must be positive")
        async with self._condition:
            # Fast path: enough tokens now
            if self._tokens >= n and not self._queue:
                self._tokens -= n
                return
            # Otherwise, enqueue request and wait
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            self._queue.append((n, fut))
            while True:
                await self._condition.wait()
                # Check if this request is at front and tokens sufficient
                if self._queue and self._queue[0][1] is fut and self._tokens >= n:
                    self._tokens -= n
                    self._queue.pop(0)
                    if not fut.done():
                        fut.set_result(True)
                    return
                # Otherwise continue waiting
                if fut.done():
                    return

    async def close(self):
        self._closed = True
        self._replenisher_task.cancel()
        try:
            await self._replenisher_task
        except asyncio.CancelledError:
            pass

# Test harness
async def _worker(limiter: AsyncTokenBucket, idx: int):
    await limiter.acquire(1)
    # Simulate some work (optional)
    return idx

async def main_test():
    limiter = AsyncTokenBucket(capacity=5, refill_rate=5)  # 5 tokens per second
    start = time.perf_counter()
    tasks = [asyncio.create_task(_worker(limiter, i)) for i in range(10)]
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start
    await limiter.close()
    print(f"Elapsed: {elapsed:.3f}s, results: {results}")
    assert abs(elapsed - 2.0) <= 0.3, f"Elapsed time {elapsed:.3f}s out of tolerance"

if __name__ == "__main__":
    asyncio.run(main_test())
