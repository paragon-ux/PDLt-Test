PARSE the universe U and the sets S1 through S9
CONSTRUCT an exact cover matrix representing set membership
INITIALIZE dancing-links data structures for the matrix
EXECUTE Knuth's Algorithm X with dancing links to enumerate all exact covers
FOR each exact cover discovered
    COLLECT the subcollection of sets forming the cover
ENDFOR
VERIFY each collected subcollection by testing that every element of U appears exactly once
EMIT the validated list of exact-cover subcollections
