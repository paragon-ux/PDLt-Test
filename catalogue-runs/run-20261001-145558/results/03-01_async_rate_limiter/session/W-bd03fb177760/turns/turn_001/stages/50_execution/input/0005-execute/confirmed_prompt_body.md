READ the async token-bucket rate limiter requirements
CONFIGURE max tokens (burst capacity) and refill rate (tokens per second)
PROVIDE an async acquire(n=1) method that waits until n tokens are available and consumes them without busy-waiting using Event or Condition
ENSURE multiple concurrent coroutines calling acquire() are served fairly with FIFO ordering
INCLUDE a test that launches 10 concurrent coroutines each requesting 1 token with a rate limit of 5 tokens/sec
VERIFY that the total elapsed time is approximately 2 seconds with tolerance ±0.3 seconds
