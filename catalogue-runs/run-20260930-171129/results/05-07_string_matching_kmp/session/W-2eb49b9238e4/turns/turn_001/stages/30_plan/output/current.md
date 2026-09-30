READ the pattern "ABABCABAB"
BUILD the failure function (partial match table) for the pattern
TRACE each step of the failure function construction
READ the text "ABABDAABABCABABABABCABAB"
SEARCH the text using the KMP algorithm with the constructed failure function
OUTPUT all starting indices where the pattern occurs in the text
