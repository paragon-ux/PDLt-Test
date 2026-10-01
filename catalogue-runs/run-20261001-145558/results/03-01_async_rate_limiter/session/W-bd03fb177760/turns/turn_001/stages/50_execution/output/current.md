import asyncio
from collections import deque

class AsyncTokenBucket:
    def __init__(self, max_tokens: int, refill_rate: float):
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate  # tokens per second
        self._tokens = max_tokens
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._wait_queue = deque()
        self._refill_task = asyncio.create_task(self._refill_loop())

    async def _refill_loop(self):
        # refill in small intervals to smooth rate
        interval = 0.01  # 10 ms
        tokens_per_interval = self._refill_rate * interval
        while True:
            await asyncio.sleep(interval)
            async with self._condition:
                if self._tokens < self._max_tokens:
                    self._tokens = min(self._max_tokens, self._tokens + tokens_per_interval)
                    self._condition.notify_all()

    async def acquire(self, n: int = 1):
        async with self._condition:
            # enqueue request for FIFO fairness
            fut = asyncio.get_running_loop().create_future()
            self._wait_queue.append((n, fut))
            while True:
                # check if this future is at queue head and enough tokens
                if self._wait_queue[0][1] is fut and self._tokens >= n:
                    self._tokens -= n
                    self._wait_queue.popleft()
                    fut.set_result(True)
                    self._condition.notify_all()
                    return
                await self._condition.wait()

# Test
async def _test():
    bucket = AsyncTokenBucket(max_tokens=5, refill_rate=5)  # 5 tokens/sec burst 5
    start = asyncio.get_event_loop().time()
    async def worker(i):
        await bucket.acquire(1)
        return i
    tasks = [asyncio.create_task(worker(i)) for i in range(10)]
    await asyncio.gather(*tasks)
    elapsed = asyncio.get_event_loop().time() - start
    print(f"Elapsed: {elapsed:.2f}s")
    assert abs(elapsed - 2.0) <= 0.3, f"Elapsed time {elapsed} not within tolerance"

if __name__ == "__main__":
    asyncio.run(_test())
