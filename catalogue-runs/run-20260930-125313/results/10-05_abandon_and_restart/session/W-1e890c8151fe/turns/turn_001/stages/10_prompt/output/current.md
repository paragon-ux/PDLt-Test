READ the input text to be encoded or decoded
READ the integer shift value for the Caesar cipher
IF the operation is encode THEN
SHIFT each alphabetic character in the input text forward by the shift value, wrapping around the alphabet
PRESERVE case of each character and leave non‑alphabetic characters unchanged
OUTPUT the encoded text
ELSE IF the operation is decode THEN
SHIFT each alphabetic character in the input text backward by the shift value, wrapping around the alphabet
PRESERVE case of each character and leave non‑alphabetic characters unchanged
OUTPUT the decoded text
ENDIF
