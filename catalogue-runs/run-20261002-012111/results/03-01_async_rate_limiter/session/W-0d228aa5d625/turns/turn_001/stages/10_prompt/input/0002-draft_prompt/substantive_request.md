TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement an asynchronous token‑bucket rate limiter in Python using asyncio. The limiter must allow configuration of the maximum number of tokens (burst capacity) and a refill rate expressed in tokens per second. It must provide an async method acquire(n=1) that waits until the requested number of tokens are available, then consumes them, using asyncio.Event or asyncio.Condition without busy‑waiting or polling. The implementation must serve multiple concurrent coroutines fairly, preserving FIFO ordering for acquire calls. A test must be included that launches ten concurrent coroutines each requesting one token, with a rate limit of five tokens per second, and verifies that the total elapsed time is approximately two seconds with a tolerance of plus or minus 0.3 seconds.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- asyncio
- burst capacity
- refill rate
- tokens per second
- acquire(n=1)
- asyncio.Event
- asyncio.Condition
- FIFO ordering
