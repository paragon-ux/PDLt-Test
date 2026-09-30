DIAGNOSE the Python program by reviewing the lock acquisition sequences in transfer_ab and transfer_ba
IDENTIFY that transfer_ab acquires lock_a then lock_b while transfer_ba acquires lock_b then lock_a, creating a circular wait condition
EXPLAIN the lock ordering violation that leads to intermittent deadlock
DESIGN a consistent lock acquisition order (e.g., always acquire lock_a before lock_b) to break the circular wait
IMPLEMENT corrected versions of transfer_ab and transfer_ba that enforce the chosen ordering
WRITE a test script that starts multiple threads invoking the original transfer functions in opposite orders to demonstrate the deadlock risk
EXECUTE the test on the original code and observe hanging behavior
EXECUTE the same test on the corrected code and verify that all threads complete without hanging
