DIAGNOSE the lock acquisition sequence in transfer_ab and transfer_ba functions
IDENTIFY the order in which lock_a and lock_b are acquired in each function
DETECT the circular wait condition arising from opposite lock ordering
EXPLAIN the lock ordering violation that leads to deadlock
DEVELOP a corrected program version that acquires locks in a consistent order (e.g., lock_a then lock_b) in both transfer_ab and transfer_ba
IMPLEMENT the corrected transfer functions with unified lock acquisition
CREATE a test harness that
    SPAWNS 100 threads invoking transfer_ab
    SPAWNS 100 threads invoking transfer_ba
    STARTS all threads
    JOINS all threads with a timeout of 5 seconds
RUN the test harness against the original program to demonstrate deadlock risk
RUN the test harness against the corrected program to verify no deadlock occurs within the timeout
REPORT the findings of the original deadlock demonstration and the corrected program verification
