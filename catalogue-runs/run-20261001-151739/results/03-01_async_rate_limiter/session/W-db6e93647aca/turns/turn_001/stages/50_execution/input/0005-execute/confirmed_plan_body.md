GATHER the functional requirements from the prompt
DESIGN a token bucket abstraction supporting a maximum burst capacity and a refill rate expressed in tokens per second
CONFIGURE the token bucket with the specified capacity and refill rate
SCHEDULE a periodic asynchronous refill task that increments the token count up to capacity at the defined rate
IMPLEMENT an async ACQUIRE method that:
    WAIT until the requested number of tokens are available using an asyncio.Event or asyncio.Condition without busy‑waiting
    ENSURE FIFO order for pending ACQUIRE calls
    CONSUME the tokens once available
SETUP a test harness that:
    CREATE a token bucket instance with a burst capacity and a refill rate of five tokens per second
    LAUNCH ten concurrent coroutines each invoking ACQUIRE(1)
    RECORD the start time
    AWAIT completion of all coroutines
    RECORD the end time
    CALCULATE the elapsed duration
VERIFY that the elapsed duration is approximately two seconds with a tolerance of ±0.3 seconds
REPORT the verification outcome
