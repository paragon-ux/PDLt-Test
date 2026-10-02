PARSE the two input arrays nums1 and nums2
DETERMINE the lengths m and n of the arrays
IF m > n THEN SWAP nums1 with nums2 and swap m with n
SET low to 0 and high to m
WHILE low <= high DO
    CALCULATE partitionX as the integer midpoint of low and high
    CALCULATE partitionY as (m + n + 1) / 2 minus partitionX
    IDENTIFY maxLeftX, minRightX, maxLeftY, and minRightY using array boundaries
    IF maxLeftX <= minRightY AND maxLeftY <= minRightX THEN
        IF (m + n) is even THEN
            COMPUTE median as the average of the greater of maxLeftX and maxLeftY and the lesser of minRightX and minRightY
        ELSE
            COMPUTE median as the greater of maxLeftX and maxLeftY
        ENDIF
        BREAK the loop
    ELSE IF maxLeftX > minRightY THEN
        SET high to partitionX - 1
    ELSE
        SET low to partitionX + 1
    ENDIF
ENDWHILE
RETURN the computed median
FOR each provided test case DO
    INVOKE the median computation with the test case inputs
    COMPARE the returned median to the expected median value
    LOG whether the test case passes or fails
END_FOR
OUTPUT the aggregate verification results
