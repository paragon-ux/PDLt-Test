IMPLEMENT an asynchronous token-bucket rate limiter using Python and asyncio.
CONFIGURE the limiter with a burst capacity and a refill rate expressed in tokens per second.
DEFINE an async method acquire(n=1) that waits until the requested number of tokens are available, then consumes them, using asyncio.Event or asyncio.Condition without busy-waiting.
ENSURE the limiter serves multiple concurrent coroutines fairly, preserving FIFO ordering for acquire calls.
INCLUDE a test that launches ten concurrent coroutines each requesting one token, with a rate limit of five tokens per second, and verifies that the total elapsed time is approximately two seconds with a tolerance of plus or minus 0.3 seconds.
