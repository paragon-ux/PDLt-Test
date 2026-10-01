TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement an asynchronous token‑bucket rate limiter in Python using asyncio. The limiter must allow configuration of a maximum token capacity (burst capacity) and a refill rate in tokens per second. It must expose an async method acquire(n=1) that waits until the requested number of tokens are available and then consumes them, using asyncio.Event or asyncio.Condition without busy‑waiting. The implementation must ensure fairness for multiple concurrent coroutines, preserving FIFO ordering of acquire requests. Provide a test that launches ten concurrent coroutines each requesting one token with the limiter set to five tokens per second, and verify that the total elapsed time is approximately two seconds with a tolerance of ±0.3 seconds.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- asyncio
- burst capacity
- refill rate
- tokens per second
- acquire
- n=1
- asyncio.Event
- asyncio.Condition
- FIFO ordering
