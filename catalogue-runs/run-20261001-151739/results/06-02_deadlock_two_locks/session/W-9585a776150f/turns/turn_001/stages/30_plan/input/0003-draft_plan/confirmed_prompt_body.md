ANALYZE the Python program that declares global threading.Lock objects lock_a and lock_b, a shared list results, and functions transfer_ab(amount) and transfer_ba(amount) which acquire the locks in opposite order before appending a tuple to results.
IDENTIFY the intermittent deadlock caused by the inconsistent lock acquisition order.
EXPLAIN the lock ordering violation and how it leads to deadlock.
PROVIDE a corrected version of the code that avoids deadlock by enforcing a consistent lock ordering (or by using a single lock).
CREATE a test that demonstrates the deadlock risk in the original code using 100 thread pairs and a join timeout of 5 seconds.
VERIFY that the corrected version runs without hanging within the join timeout of 5 seconds for 100 thread pairs.
INCLUDE all operative task entities: lock_a, lock_b, results, transfer_ab, transfer_ba, join, 100, 5.
