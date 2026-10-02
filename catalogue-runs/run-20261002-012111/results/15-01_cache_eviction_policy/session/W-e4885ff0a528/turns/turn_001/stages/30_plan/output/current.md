FOR EACH policy IN [LRU, LFU, ARC]
    INITIALIZE a cache of capacity 5 using the policy
    SET hit_count = 0
    SET miss_count = 0
    FOR EACH request IN the access sequence
        IF request IS IN cache THEN
            INCREMENT hit_count
        ELSE
            INCREMENT miss_count
            INSERT request into cache according to the policy's eviction rule
        ENDIF
        RECORD cache state after this request
    ENDFOR
    COMPUTE hit_rate = hit_count / total_requests
    STORE hit_count, miss_count, and hit_rate for the policy
ENDFOR
COMPARE hit_rates across policies
IDENTIFY the policy with the highest hit_rate
EXPLAIN why that policy yields the highest hit_rate based on its eviction behavior and the access pattern
