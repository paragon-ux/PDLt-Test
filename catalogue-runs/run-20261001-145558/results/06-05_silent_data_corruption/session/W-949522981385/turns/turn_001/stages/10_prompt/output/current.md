READ the Python struct packing code that defines a record with fields uint32 user_id, bool active, and float64 score
ANALYZE the alignment and padding that cause the packed size to exceed 13 bytes
EXPLAIN why the packed size may not be 13 bytes and why values may be read incorrectly due to default alignment rules
PROVIDE a fix that ensures the packed size is exactly 13 bytes and that values are correctly recovered when unpacked
INCLUDE the following operative task entities verbatim: struct, user_id, active, score, uint32, bool, float64, padding, alignment
