def fibonacci_iterative(n: int):
    """Return a list containing the Fibonacci sequence up to n terms.
    Args:
        n (int): Number of terms to generate. Must be non‑negative.
    Returns:
        List[int]: Fibonacci sequence of length n.
    """
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq
