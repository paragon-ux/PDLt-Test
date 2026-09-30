# Implementation placeholder for the requested sorting algorithm
# The requirements specify a comparison‑based sort with O(n) worst‑case time, stability, and in‑place O(1) extra space.
# Such a combination is provably impossible for comparison‑based sorts (the comparison lower bound is Ω(n log n)).
# Consequently, the implementation cannot satisfy the O(n) worst‑case time constraint while remaining comparison‑based.
# The following function raises a NotImplementedError to indicate that the required algorithm cannot be provided.

def sort_in_place(arr):
    """Sort the list *arr* in‑place.
    
    The function is defined to match the requested signature, but the algorithm that meets all
    constraints does not exist. Calling this function will raise a NotImplementedError.
    """
    raise NotImplementedError(
        "A comparison‑based, stable, in‑place sort with O(n) worst‑case time complexity is not possible."
    )

# Example usage (will raise the exception):
# data = [3, 1, 2, 1]
# sort_in_place(data)
