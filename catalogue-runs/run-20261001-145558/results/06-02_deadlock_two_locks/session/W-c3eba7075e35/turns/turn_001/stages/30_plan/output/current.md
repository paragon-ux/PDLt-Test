READ the Python program containing functions transfer_ab and transfer_ba with locks lock_a and lock_b
IDENTIFY the inconsistent lock ordering between the two functions
EXPLAIN the lock ordering violation that can cause intermittent deadlock
CREATE a corrected version of both functions where locks are acquired in the global order lock_a then lock_b
WRITE a test that invokes transfer_ab and transfer_ba concurrently to demonstrate the deadlock risk in the original code
WRITE a test that invokes the corrected functions concurrently to verify they complete without hanging
