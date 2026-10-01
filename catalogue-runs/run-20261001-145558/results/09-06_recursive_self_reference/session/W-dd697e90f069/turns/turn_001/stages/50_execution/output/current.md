# Modified PDL Rules
# PDL-02: Allow multiple operations per line, separated by semicolons.
# PDL-05: Permit the use of TASK: and OUTPUT: field prefixes.

# Pseudocode using the modified rules
TASK: READ the list of integers; SORT the list using MERGE SORT; OUTPUT the sorted list

# Implementation details
# READ: Assume input list is provided as variable `input_list`.
# MERGE SORT algorithm:
#   FUNCTION merge_sort(arr):
#       IF length of arr <= 1 RETURN arr
#       mid = length(arr) // 2
#       left = merge_sort(arr[0:mid])
#       right = merge_sort(arr[mid:])
#       RETURN merge(left, right)
#   FUNCTION merge(left, right):
#       result = []
#       WHILE left and right:
#           IF left[0] <= right[0]:
#               result.append(left.pop(0))
#           ELSE:
#               result.append(right.pop(0))
#       result.extend(left or right)
#       RETURN result
#   sorted_list = merge_sort(input_list)
# OUTPUT: Print or return `sorted_list`.
