READ the requirements for an async token-bucket rate limiter using asyncio
CONFIGURE the token bucket with a maximum burst capacity and a refill rate in tokens per second
PROVIDE an async acquire(n=1) method that waits until n tokens are available and then consumes them without busy-waiting, using asyncio synchronization primitives
ENSURE that multiple concurrent coroutines calling acquire() are served fairly in FIFO order
INCLUDE a test that launches 10 concurrent coroutines each requesting 1 token with a rate limit of 5 tokens per second and verifies that the total elapsed time is approximately 2 seconds (±0.3 seconds tolerance)
EMBED the operative task entities verbatim: acquire, asyncio, 5, 10, token-bucket
