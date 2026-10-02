EXPLAIN why struct.pack with format 'I?d' may produce a packed size larger than 13 bytes because the default native alignment inserts padding after the bool/uint8 active field.
DESCRIBE how the padding aligns the subsequent float64 score on an 8‑byte boundary, resulting in a total size of 16 bytes instead of the expected 13 bytes.
PROVIDE corrected Python code that uses struct.pack with a standard size, no‑alignment format prefix '<' to pack the fields user_id, active, and score into exactly 13 bytes, and uses struct.unpack with the same format to read the values back.
SHOW that the packed result length is 13 bytes and that the unpacked values (user_id, active, score) exactly match the original inputs, confirming a correct round‑trip.
