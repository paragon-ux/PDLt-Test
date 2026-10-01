READ the async token-bucket rate limiter requirements
CONFIGURE a token bucket with specified max tokens (burst capacity) and refill rate (tokens per second)
IMPLEMENT an async refill coroutine that adds tokens at the refill rate while respecting the max token limit
CREATE an async acquire(n=1) method that:
    ACQUIRE a lock or condition
    WAIT until the bucket contains at least n tokens using await on the condition without busy‑waiting
    DECREMENT the token count by n
    NOTIFY waiting coroutines to preserve FIFO ordering
ENSURE FIFO fairness by maintaining a queue of waiting coroutines and waking them in order
WRITE a test that:
    SET the rate limit to 5 tokens/second
    LAUNCH 10 concurrent coroutines each invoking acquire(1)
    MEASURE the total elapsed time
    ASSERT the elapsed time is approximately 2 seconds with tolerance ±0.3 seconds
