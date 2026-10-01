Implement an async token-bucket rate limiter in Python using asyncio with these requirements:
1. Configure max tokens (burst capacity) and refill rate (tokens per second).
2. acquire(n=1) is an async method that waits until n tokens are available, then consumes them. No busy-waiting or polling — use asyncio.Event or asyncio.Condition.
3. Multiple concurrent coroutines calling acquire() must be served fairly (FIFO ordering).
4. Include a test that launches 10 concurrent coroutines each requesting 1 token with a rate limit of 5 tokens/sec, and verifies that the total elapsed time is approximately 2 seconds (±0.3s tolerance).
