READ the Python code defining the function pack_record(user_id, active, score) that uses struct format string 'I?d'
READ the Python code defining the function unpack_record(data) that uses struct format string 'I?d'
ANALYZE the struct packing alignment and padding issue that may cause the packed size to exceed the expected 13 bytes
EXPLAIN why native alignment padding can make the packed size larger than 13 bytes
EXPLAIN why recovered values can be incorrect due to alignment padding affecting the uint32, bool/uint8, and float64 fields
PROVIDE a corrected implementation for pack_record and unpack_record that explicitly controls padding, ensuring a 13‑byte representation and accurate values
USE an explicit little‑endian standard size format such as '<I?d' or add explicit padding bytes as needed
INCLUDE the following task entities verbatim in the prompt: pack_record, unpack_record, struct, I?d, user_id, active, score, uint32, bool/uint8, float64
