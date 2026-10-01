READ the supplied Python code defining pack_record and unpack_record
EXTRACT the struct format strings used in pack_record and unpack_record
DETERMINE the actual packed byte size produced by struct.pack with the default native format
CALCULATE the expected size based on the constituent types (unsigned int, boolean, double) without padding
IDENTIFY any padding bytes inserted by the default native format to align the double on an 8‑byte boundary
EXPLAIN that the added padding causes the packed size to exceed the expected 13 bytes and may misalign unpack offsets
SELECT an explicit format that eliminates native padding, such as '=I?d' or '<I?d', or alternatively insert an explicit padding byte using 'I?xd'
UPDATE pack_record to use the chosen explicit format for packing the values
UPDATE unpack_record to use the same explicit format for unpacking the values
VERIFY that the packed size matches the expected 13 bytes and that unpacking reproduces the original values correctly
