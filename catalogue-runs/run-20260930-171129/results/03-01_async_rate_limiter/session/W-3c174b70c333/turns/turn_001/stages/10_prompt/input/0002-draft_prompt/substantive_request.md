TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement an async token-bucket rate limiter in Python using asyncio with these requirements: configure max tokens (burst capacity) and refill rate (tokens per second); provide an async acquire(n=1) method that waits until n tokens are available and then consumes them without busy-waiting, using asyncio synchronization primitives; ensure multiple concurrent coroutines calling acquire() are served fairly in FIFO order; include a test that launches 10 concurrent coroutines each requesting 1 token with a rate limit of 5 tokens per second and verifies that total elapsed time is approximately 2 seconds (±0.3s tolerance).
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- acquire
- asyncio
- 5
- 10
- token-bucket
