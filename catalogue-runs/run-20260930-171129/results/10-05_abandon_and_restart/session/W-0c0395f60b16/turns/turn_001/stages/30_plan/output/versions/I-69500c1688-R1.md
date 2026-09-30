RECEIVE input text and integer shift value for encoding
VALIDATE that shift is an integer
FOR each character in the input text
IF character is alphabetic
DETERMINE its case (uppercase or lowercase)
SHIFT the character forward by the given offset within the alphabet, wrapping around as needed
PRESERVE original case in the result
ELSE
PRESERVE the character unchanged
OUTPUT the resulting encoded text

RECEIVE input text and integer shift value for decoding
VALIDATE that shift is an integer
FOR each character in the input text
IF character is alphabetic
DETERMINE its case (uppercase or lowercase)
SHIFT the character backward by the given offset within the alphabet, wrapping around as needed
PRESERVE original case in the result
ELSE
PRESERVE the character unchanged
OUTPUT the resulting decoded text
