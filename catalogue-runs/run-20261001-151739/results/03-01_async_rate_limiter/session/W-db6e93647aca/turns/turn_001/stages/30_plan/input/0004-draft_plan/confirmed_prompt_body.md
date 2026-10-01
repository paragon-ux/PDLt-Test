NOTE ENTITIES: Python, asyncio, acquire(n=1), acquire(), asyncio.Event, asyncio.Condition
IMPLEMENT an asynchronous token bucket rate limiter USING Python and asyncio
CONFIGURE a maximum token capacity (burst capacity) and a refill rate expressed in tokens per second
PROVIDE an async method acquire(n=1) THAT waits until n tokens are available WITHOUT busy-waiting USING asyncio.Event OR asyncio.Condition, THEN consumes the tokens
ENSURE that multiple concurrent coroutines calling acquire() are served in FIFO order
INCLUDE a test THAT launches ten concurrent coroutines each requesting one token with a rate limit of five tokens per second
VERIFY that the total elapsed time is approximately two seconds with tolerance plus or minus 0.3 seconds
