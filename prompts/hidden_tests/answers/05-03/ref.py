def insert_interval(intervals, new_interval):
    result, i, n = [], 0, len(intervals)
    lo, hi = new_interval
    while i < n and intervals[i][1] < lo:
        result.append(list(intervals[i]))
        i += 1
    while i < n and intervals[i][0] <= hi:
        lo, hi = min(lo, intervals[i][0]), max(hi, intervals[i][1])
        i += 1
    result.append([lo, hi])
    result.extend(list(x) for x in intervals[i:])
    return result
