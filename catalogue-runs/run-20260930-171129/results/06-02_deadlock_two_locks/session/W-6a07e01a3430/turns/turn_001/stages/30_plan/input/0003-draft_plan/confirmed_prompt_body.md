DIAGNOSE the intermittent deadlock in the provided Python program that uses two locks (lock_a and lock_b) with opposite acquisition orders in transfer_ab and transfer_ba.
EXPLAIN the lock ordering violation that causes the deadlock.
PROVIDE a corrected version of the code that avoids deadlock by enforcing a consistent lock acquisition order.
INCLUDE a test that demonstrates the deadlock risk in the original code.
VERIFY that the fixed code runs without hanging.
