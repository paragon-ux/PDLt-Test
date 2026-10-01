DESIGN frequency-to-key linked lists and key-to-node map structures
INITIALIZE cache with capacity, frequency map, and recency order trackers
IMPLEMENT get(key) operation:
    IF key exists THEN
        RETURN value and UPDATE its frequency count and position in frequency list
    ELSE
        RETURN indication of miss
IMPLEMENT put(key, value) operation:
    IF key exists THEN
        UPDATE value and treat as accessed (update frequency)
    ELSE
        IF cache at capacity THEN
            EVICT least frequently used key using LRU tie-breaking from lowest frequency list
        INSERT new key with frequency count 1 into appropriate structures
    ENDIF
ENSURE frequency counts are incremented on each get or put access
MAINTAIN LRU ordering within each frequency level for tie-breaking
DEVELOP self‑contained test suite:
    CREATE tests for capacity limit enforcement and proper eviction
    CREATE tests for frequency count updates after accesses
    CREATE tests for LRU tie‑breaking when frequencies match
    RUN test suite to validate correctness
