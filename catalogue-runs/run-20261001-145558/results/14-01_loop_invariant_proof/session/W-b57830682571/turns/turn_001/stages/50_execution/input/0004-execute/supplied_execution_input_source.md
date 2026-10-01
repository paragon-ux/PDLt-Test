Given the following loop that computes the sum of an array:

`python
def array_sum(arr):
    total = 0
    i = 0
    while i < len(arr):
        total = total + arr[i]
        i = i + 1
    return total
`

State the loop invariant that holds at the beginning of each iteration. Prove that: (1) the invariant holds before the first iteration (initialization), (2) if the invariant holds before an iteration, it holds after (maintenance), and (3) when the loop terminates, the invariant implies the correct result (termination). Write a version of the function with assert statements that mechanically check the invariant at each iteration.
