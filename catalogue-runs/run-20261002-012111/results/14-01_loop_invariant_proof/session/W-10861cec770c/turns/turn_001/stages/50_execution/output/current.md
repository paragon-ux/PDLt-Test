def array_sum(arr):
    total = 0
    i = 0
    # Loop invariant: At the start of each iteration, total == sum(arr[0:i])
    while i < len(arr):
        # Assert the invariant holds before this iteration
        assert total == sum(arr[:i]), "Loop invariant violated before iteration"
        total = total + arr[i]
        i = i + 1
        # Assert the invariant holds after this iteration (i has been incremented)
        assert total == sum(arr[:i]), "Loop invariant violated after iteration"
    return total
