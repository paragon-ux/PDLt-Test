DEFINE async token‑bucket rate limiter class
  CONFIGURE it with maximum token capacity (burst capacity) and a refill rate in tokens per second
  INITIALIZE internal token count to the configured capacity
  CREATE an asyncio.Condition to coordinate waiting coroutines
  START a background refill coroutine
    REPEATEDLY compute tokens to add based on elapsed time and refill rate, up to capacity
    UPDATE token count and NOTIFY waiting coroutines
  IMPLEMENT async acquire(n=1) method
    ENQUEUE acquire request preserving FIFO order to ensure fairness
    WHILE requested tokens are unavailable
      WAIT on the condition
    CONSUME the requested tokens
    RETURN control to the caller
  PROVIDE cleanup method to cancel the background refill task
WRITE asynchronous test function
  INSTANTIATE the limiter with a burst capacity and a refill rate of five tokens per second
  RECORD start time
  LAUNCH ten concurrent coroutines, each invoking acquire(1)
  AWAIT completion of all coroutines
  RECORD end time
  CALCULATE elapsed time
  ASSERT that elapsed time is approximately two seconds within a tolerance of ±0.3 seconds
VERIFY that the implementation avoids busy‑waiting and relies on condition notification
