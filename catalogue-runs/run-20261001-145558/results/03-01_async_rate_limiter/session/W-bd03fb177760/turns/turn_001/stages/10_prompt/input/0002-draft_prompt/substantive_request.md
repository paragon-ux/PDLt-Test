TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement an async token-bucket rate limiter in Python using asyncio with these requirements: configure max tokens (burst capacity) and refill rate (tokens per second); provide an async acquire(n=1) method that waits until n tokens are available and then consumes them without busy-waiting, using asyncio.Event or asyncio.Condition; ensure multiple concurrent coroutines calling acquire() are served fairly (FIFO ordering); include a test that launches 10 concurrent coroutines each requesting 1 token with a rate limit of 5 tokens/sec, and verifies that the total elapsed time is approximately 2 seconds (±0.3s tolerance).
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- async
- token-bucket
- rate limiter
- Python
- asyncio
- max tokens
- burst capacity
- refill rate
- tokens per second
- acquire
- n=1
- Event
- Condition
- FIFO ordering
- test
- 10 concurrent coroutines
- 1 token
- 5 tokens/sec
- 2 seconds
- ±0.3s
