# Correct with a different interface: a dict result, string first.
def longest_common_subsequence(a, b):
    table = [[""] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            if a[i] == b[j]:
                table[i][j] = a[i] + table[i + 1][j + 1]
            else:
                left, down = table[i + 1][j], table[i][j + 1]
                table[i][j] = left if len(left) >= len(down) else down
    return {"subsequence": table[0][0], "length": len(table[0][0])}
