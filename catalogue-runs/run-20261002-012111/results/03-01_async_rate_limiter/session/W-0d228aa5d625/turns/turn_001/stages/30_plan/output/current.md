DEFINE a token bucket rate limiter class with parameters capacity and refill_rate
INITIALIZE the internal token count to the burst capacity
CREATE a FIFO queue to hold pending acquire requests
START an asynchronous replenisher coroutine that
    WHILE true DO
        WAIT for the interval derived from the refill_rate
        INCREMENT token count up to capacity
        NOTIFY waiting coroutines via a condition/event
IMPLEMENT an async acquire method that
    IF token count >= requested n THEN
        DECREMENT token count by n
        RETURN immediately
    ELSE
        ENQUEUE the request (including n and a condition) in the FIFO queue
        WAIT on the associated condition/event until notified
        WHEN notified AND request is at the head of the queue AND token count >= n THEN
            DEQUEUE request
            DECREMENT token count by n
            RESUME coroutine
ENSURE FIFO ordering of acquisitions by processing queued requests in order
UTILIZE asyncio.Condition or asyncio.Event to coordinate without busy-waiting
DEVELOP a test harness that
    CONFIGURE the limiter with a burst capacity and a refill rate of five tokens per second
    LAUNCH ten concurrent coroutines each calling acquire(1)
    MEASURE elapsed time from start to completion of all coroutines
    VERIFY that elapsed time is approximately two seconds within a tolerance of ±0.3 seconds
RETURN the test result for validation
