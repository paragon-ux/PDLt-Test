FOR each test case containing nums1 and nums2 DO
    IF length(nums1) > length(nums2) THEN
        SWAP nums1 and nums2
    ENDIF
    SET totalLength = length(nums1) + length(nums2)
    SET low = 0
    SET high = length(nums1)
    WHILE low <= high
        CALCULATE partitionX = (low + high) // 2
        CALCULATE partitionY = (totalLength + 1) // 2 - partitionX
        DETERMINE maxLeftX = IF partitionX == 0 THEN -infinity ELSE nums1[partitionX-1] ENDIF
        DETERMINE minRightX = IF partitionX == length(nums1) THEN +infinity ELSE nums1[partitionX] ENDIF
        DETERMINE maxLeftY = IF partitionY == 0 THEN -infinity ELSE nums2[partitionY-1] ENDIF
        DETERMINE minRightY = IF partitionY == length(nums2) THEN +infinity ELSE nums2[partitionY] ENDIF
        IF maxLeftX <= minRightY AND maxLeftY <= minRightX THEN
            IF totalLength MOD 2 == 0 THEN
                SET median = (MAX(maxLeftX, maxLeftY) + MIN(minRightX, minRightY)) / 2
            ELSE
                SET median = MAX(maxLeftX, maxLeftY)
            ENDIF
            BREAK
        ELSE IF maxLeftX > minRightY THEN
            SET high = partitionX - 1
        ELSE
            SET low = partitionX + 1
        ENDIF
    ENDWHILE
    OUTPUT median
END_FOR
