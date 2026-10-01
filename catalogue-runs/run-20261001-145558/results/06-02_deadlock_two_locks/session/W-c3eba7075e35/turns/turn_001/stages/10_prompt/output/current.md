READ the Python program containing functions transfer_ab and transfer_ba with locks lock_a and lock_b
IDENTIFY the inconsistent lock ordering causing intermittent deadlock
EXPLAIN the lock ordering violation between transfer_ab and transfer_ba
CREATE a corrected version where both functions acquire the locks in a consistent global order (acquire lock_a then lock_b)
INCLUDE a test that demonstrates the deadlock risk in the original code using transfer_ab and transfer_ba
INCLUDE a test that verifies the fixed code runs without hanging
