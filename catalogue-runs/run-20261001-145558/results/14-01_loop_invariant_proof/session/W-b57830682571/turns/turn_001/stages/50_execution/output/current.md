def array_sum(arr):
    """
    Compute the sum of the elements in `arr`.
    Loop invariant: At the start of each iteration (including the first),
    `total` equals the sum of the elements of `arr` up to index `i-1`.
    That is, total == sum(arr[0:i])
    """
    total = 0
    i = 0
    # Invariant holds before the first iteration
    assert total == sum(arr[:i]), "Initialization invariant violated"
    while i < len(arr):
        # Maintenance: before body, invariant holds
        assert total == sum(arr[:i]), "Invariant before iteration violated"
        total = total + arr[i]
        i = i + 1
        # After body, invariant holds for next iteration
        assert total == sum(arr[:i]), "Invariant after iteration violated"
    # Upon termination, i == len(arr), so total == sum(arr)
    assert total == sum(arr), "Termination invariant violated"
    return total
