DEFINE a Python class representing the LFU cache with constructor parameters for capacity.
DEFINE internal data structures: a key-to-node map, a frequency-to-ordered-nodes map, and a minimum-frequency tracker.
IMPLEMENT the get(key) method to retrieve the value, update its frequency, and reposition the entry in O(1) time.
IMPLEMENT the put(key, value) method to insert or update entries, handle capacity overflow by evicting the least frequently used key, using LRU tie-breaking when frequencies match, all in O(1) time.
ENSURE frequency counters are incremented on each get or put access.
INCLUDE a self-contained test suite that:
    CREATE instances of the LFU cache with various capacities.
    VERIFY that get and put operations behave as specified.
    VALIDATE that capacity limits trigger correct eviction of the least frequently used entries.
    CONFIRM that frequency updates occur correctly after accesses.
    CONFIRM that when multiple keys share the minimum frequency, the least recently used among them is evicted.
EXECUTE the test suite and report pass/fail results.
