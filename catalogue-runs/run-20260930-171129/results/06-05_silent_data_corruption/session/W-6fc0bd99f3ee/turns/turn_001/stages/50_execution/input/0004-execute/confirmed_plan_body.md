EXPLAIN why struct.pack with format "I?d" yields a buffer larger than 13 bytes due to default alignment and padding rules
DESCRIBE the alignment requirements of uint32, uint8, and float64 that cause padding bytes to be inserted between the fields
ANALYZE how the struct module interprets the format string "I?d" under native byte order and standard size/alignment
SPECIFY the need for explicit padding control to achieve a deterministic 13‑byte layout
PROPOSE a corrected format string that disables native alignment (e.g., using "<" or "=") and inserts manual padding bytes where required
OUTLINE example code that:
PACK the three fields (uint32 user_id, uint8 active flag, float64 score) into exactly 13 bytes using the corrected format
UNPACK the resulting 13‑byte buffer back into the original values
VALIDATE that the packed length is 13 and that unpacked values match the inputs
PREPARE the final deliverable containing the explanatory text and the example code snippet
