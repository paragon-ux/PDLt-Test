RECEIVE the two sorted integer arrays nums1 and nums2.
VALIDATE that both inputs are integer arrays sorted in non‑decreasing order.
IF the length of nums1 exceeds the length of nums2 THEN SWAP nums1 and nums2.
SET low to 0 and high to the length of nums1.
WHILE low <= high DO
    CALCULATE partitionX as the integer midpoint of low and high.
    CALCULATE partitionY as (total length + 1) // 2 minus partitionX.
    DETERMINE maxLeftX, minRightX, maxLeftY, minRightY using the partition indices, treating out‑of‑range positions as -infinity or +infinity.
    IF maxLeftX <= minRightY AND maxLeftY <= minRightX THEN
        IF total number of elements is odd THEN
            SET median to the larger of maxLeftX and maxLeftY.
        ELSE
            SET median to the average of the larger of maxLeftX and maxLeftY and the smaller of minRightX and minRightY.
        ENDIF
        EXIT WHILE.
    ELSE IF maxLeftX > minRightY THEN
        SET high to partitionX - 1.
    ELSE
        SET low to partitionX + 1.
    ENDIF
ENDWHILE
RETURN the median as a floating‑point value.
VALIDATE the returned median against each provided test case to confirm correctness.
