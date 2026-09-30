VALIDATE that nums1 and nums2 are provided and are sorted sequences
IDENTIFY the shorter of the two sequences and assign it to A, the other to B
INITIALIZE low to 0 and high to length of A
WHILE low <= high
SET partitionA = (low + high) // 2
SET partitionB = (len(A) + len(B) + 1) // 2 - partitionA
DETERMINE maxLeftA = -infinity if partitionA == 0 else A[partitionA - 1]
DETERMINE minRightA = +infinity if partitionA == len(A) else A[partitionA]
DETERMINE maxLeftB = -infinity if partitionB == 0 else B[partitionB - 1]
DETERMINE minRightB = +infinity if partitionB == len(B) else B[partitionB]
IF maxLeftA <= minRightB AND maxLeftB <= minRightA
IF (len(A) + len(B)) is odd
SET median = max(maxLeftA, maxLeftB)
ELSE
SET median = (max(maxLeftA, maxLeftB) + min(minRightA, minRightB)) / 2
ENDIF
BREAK loop
ELSE IF maxLeftA > minRightB
SET high = partitionA - 1
ELSE
SET low = partitionA + 1
ENDIF
ENDWHILE
OUTPUT the computed median as a numeric result
