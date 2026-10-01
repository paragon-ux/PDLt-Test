TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement an asynchronous token-bucket rate limiter in Python using asyncio. Configure a maximum token capacity (burst capacity) and a refill rate expressed in tokens per second. Provide an async method acquire(n=1) that waits until n tokens are available without busy-waiting, using asyncio.Event or asyncio.Condition, then consumes the tokens. Ensure that multiple concurrent coroutines calling acquire() are served in FIFO order. Include a test that launches ten concurrent coroutines each requesting one token with a rate limit of five tokens per second, and verify that the total elapsed time is approximately two seconds within a tolerance of plus or minus 0.3 seconds.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- asyncio
- acquire(n=1)
- acquire()
- asyncio.Event
- asyncio.Condition
