ANALYZE the supplied Python program to extract the definitions of lock_a, lock_b, results, transfer_ab, and transfer_ba.
IDENTIFY any inconsistent lock acquisition ordering between transfer_ab and transfer_ba.
EXPLAIN the lock ordering violation and how it can cause an intermittent deadlock.
DESIGN a corrected version of the code that enforces a consistent lock ordering or consolidates lock usage into a single lock.
IMPLEMENT the corrected code according to the design.
CREATE a test harness that launches 100 pairs of threads invoking transfer_ab and transfer_ba on the original code and joins each thread with a timeout of 5 seconds.
EXECUTE the test harness on the original code to observe the potential deadlock.
CREATE a test harness that launches 100 pairs of threads invoking transfer_ab and transfer_ba on the corrected code and joins each thread with a timeout of 5 seconds.
EXECUTE the test harness on the corrected code to verify completion without hanging within the timeout.
OUTPUT the analysis, explanation, corrected code, and verification results.
