TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a Python function that computes the longest common subsequence (LCS) of two input strings s1 and s2 using dynamic programming. The function must return both the length of the LCS and the LCS string itself. The solution should build a DP table of LCS lengths, then reconstruct the subsequence by backtracking through the table. Include tests: with s1 = "AGGTAB" and s2 = "GXTXAYB" the LCS should be "GTAB" with length 4; also test identical strings, one empty string, and strings with no common characters.
APPROACH/RISK NOTES:
Use a bottom‑up DP table to compute LCS lengths, then iterate from the bottom‑right corner to backtrack and build the LCS string. Ensure edge cases (empty inputs, no common characters) are handled correctly.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- s1
- s2
- AGGTAB
- GXTXAYB
- GTAB
- 4
