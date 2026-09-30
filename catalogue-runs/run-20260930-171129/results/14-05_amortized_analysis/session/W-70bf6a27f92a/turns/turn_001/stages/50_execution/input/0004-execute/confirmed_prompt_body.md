READ dynamic array push operations starting with capacity 1, doubling capacity when a push exceeds current capacity
ASSIGN each push operation an amortized credit of 3 units
WHEN a push triggers a resize, SPEND 1 unit for the push itself and n units to copy the n existing elements, using stored credits to pay the copy cost
ENSURE the prepaid credit balance never becomes negative
PROVE that the amortized cost per push is O(1)
COMPUTE the exact amortized cost per operation as 3 units
