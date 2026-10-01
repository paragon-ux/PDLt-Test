READ the provided Python code defining pack_record and unpack_record that uses struct.pack('I?d') and struct.unpack('I?d')
DIAGNOSE the struct packing alignment and padding issue that causes the packed size to exceed the expected 13 bytes
EXPLAIN that the default native format adds padding after the boolean to align the double on an 8‑byte boundary
DESCRIBE why reading back the values can produce incorrect results because the unpack format does not account for the padding, resulting in mismatched offsets
FIX the code by using an explicit standard‑size format such as '=I?d' or '<I?d' to remove native padding, OR by inserting an explicit padding byte using a format like 'I?xd' to control alignment
UPDATE both pack_record and unpack_record functions to use the chosen format consistently
