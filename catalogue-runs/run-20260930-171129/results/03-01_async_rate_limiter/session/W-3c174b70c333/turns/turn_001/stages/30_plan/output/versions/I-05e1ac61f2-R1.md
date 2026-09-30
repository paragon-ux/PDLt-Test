DEFINE token bucket with maximum burst capacity and refill rate (tokens per second)
IMPLEMENT async acquire(n=1) method that:
WAITS until n tokens are available using asyncio synchronization primitives
CONSUMES n tokens atomically without busy-waiting
ENSURE FIFO fairness for concurrent acquire calls by queuing requests in order of arrival
SETUP test environment:
CONFIGURE rate limit to 5 tokens per second
LAUNCH 10 concurrent coroutines each requesting 1 token via acquire()
RECORD start time before launches and end time after all coroutines complete
VERIFY that elapsed time is approximately 2 seconds within ±0.3 seconds tolerance
