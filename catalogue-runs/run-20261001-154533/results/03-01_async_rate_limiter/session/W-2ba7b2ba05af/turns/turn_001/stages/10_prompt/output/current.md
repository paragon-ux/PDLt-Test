READ the request to implement an asynchronous token‑bucket rate limiter in Python using asyncio
CONFIGURE the limiter with a maximum token capacity (burst capacity) and a refill rate in tokens per second
EXPOSE an async method acquire(n=1) that waits until the requested number of tokens are available and then consumes them, using asyncio.Event or asyncio.Condition without busy‑waiting
ENSURE fairness for multiple concurrent coroutines by preserving FIFO ordering of acquire requests
PROVIDE a test that launches ten concurrent coroutines each requesting one token with the limiter set to five tokens per second
VERIFY that the total elapsed time of the test is approximately two seconds with a tolerance of ±0.3 seconds
