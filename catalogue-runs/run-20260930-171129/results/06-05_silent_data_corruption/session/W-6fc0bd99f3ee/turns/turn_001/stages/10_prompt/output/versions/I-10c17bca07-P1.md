DIAGNOSE why the struct.pack format 'I?d' does not produce a 13-byte buffer and why unpacked values may be incorrect due to alignment and padding.
EXPLAIN the alignment rules that cause struct.pack with the default format to insert padding between the uint32 user_id, the uint8 active flag, and the float64 score, resulting in a larger buffer.
DESCRIBE how the presence of the 'struct' module and the format string 'I?d' influences the layout.
PROVIDE a corrected implementation that uses explicit padding control (e.g., format string with '<' or '=' and manual padding bytes) to ensure a consistent 13-byte layout for a record containing a uint32 user_id, a uint8 active flag, and a float64 score.
INCLUDE example code that packs the three fields into exactly 13 bytes and unpacks them correctly, demonstrating the use of the specified entities: struct and I?d.
