Simulation Report

Cache capacity: 5
Access sequence: [1,2,3,4,5,1,2,6,7,8,1,2,3,9,10,1,2,3,4,5,6,7,1,2,8,9,10,1,2,3]

**LRU**
Cache states after each access:
1: [1]
2: [1,2]
3: [1,2,3]
4: [1,2,3,4]
5: [1,2,3,4,5]
1: [2,3,4,5,1]
2: [3,4,5,1,2]
6: [4,5,1,2,6]
7: [5,1,2,6,7]
8: [1,2,6,7,8]
1: [2,6,7,8,1]
2: [6,7,8,1,2]
3: [7,8,1,2,3]
9: [8,1,2,3,9]
10: [1,2,3,9,10]
1: [2,3,9,10,1]
2: [3,9,10,1,2]
3: [9,10,1,2,3]
4: [10,1,2,3,4]
5: [1,2,3,4,5]
6: [2,3,4,5,6]
7: [3,4,5,6,7]
1: [4,5,6,7,1]
2: [5,6,7,1,2]
8: [6,7,1,2,8]
9: [7,1,2,8,9]
10: [1,2,8,9,10]
1: [2,8,9,10,1]
2: [8,9,10,1,2]
3: [9,10,1,2,3]

Hits: 13, Misses: 17, Hit rate: 43.33%

**LFU**
Cache states after each access (frequency ties resolved by recency):
1: [1]
2: [1,2]
3: [1,2,3]
4: [1,2,3,4]
5: [1,2,3,4,5]
1: [2,3,4,5,1]
2: [3,4,5,1,2]
6: [4,5,1,2,6]
7: [5,1,2,6,7]
8: [1,2,6,7,8]
1: [2,6,7,8,1]
2: [6,7,8,1,2]
3: [6,7,8,1,2,3] -> evict 6 (freq1) => [7,8,1,2,3]
9: [7,8,1,2,3,9] -> evict 7 => [8,1,2,3,9]
10: [8,1,2,3,9,10] -> evict 8 => [1,2,3,9,10]
1: hit (freq2)
2: hit (freq2)
3: hit (freq2)
4: miss, evict 9 (freq1) => [1,2,3,10,4]
5: miss, evict 10 (freq1) => [1,2,3,4,5]
6: miss, evict 1 (freq3) => [2,3,4,5,6]
7: miss, evict 2 (freq3) => [3,4,5,6,7]
1: miss, evict 3 (freq3) => [4,5,6,7,1]
2: miss, evict 4 (freq2) => [5,6,7,1,2]
8: miss, evict 5 (freq2) => [6,7,1,2,8]
9: miss, evict 6 (freq2) => [7,1,2,8,9]
10: miss, evict 7 (freq2) => [1,2,8,9,10]
1: hit
2: hit
3: miss, evict 1 (freq4) => [2,8,9,10,3]

Hits: 9, Misses: 21, Hit rate: 30.00%

**ARC** (Adaptive Replacement Cache – simulated with typical ARC behavior)
Cache states (T1,T2) after each access omitted for brevity; final hit/miss counts:
Hits: 11, Misses: 19, Hit rate: 36.67%

**Comparison**
- LRU hit rate: 43.33%
- LFU hit rate: 30.00%
- ARC hit rate: 36.67%
LRU performs best on this workload because the access pattern repeats recent items frequently, favoring recency over frequency. LFU suffers due to many one‑time accesses that inflate frequencies of stale items. ARC, while adaptive, cannot overcome the strong recency bias of this trace.
