ENTITIES: transfer_ab, transfer_ba, lock_a, lock_b, 100, 5, ab, ba, i, join, timeout
DIAGNOSE the deadlock caused by opposite lock acquisition order in the transfer_ab and transfer_ba functions.
EXPLAIN the lock ordering violation that leads to a deadlock.
PROVIDE a corrected version of the program that enforces a consistent lock acquisition order for both transfer_ab and transfer_ba.
INCLUDE a test that spawns 100 threads for each direction (ab and ba) and uses join with a timeout of 5 seconds to demonstrate the deadlock risk in the original code.
VERIFY that the corrected code runs without hanging under the same test conditions.
