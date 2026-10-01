READ the sorted list of non-overlapping intervals
READ the new interval
INSERT the new interval into the list preserving sorted order
MERGE any overlapping intervals resulting from the insertion
RETURN the resulting sorted list of intervals
PROVIDE tests covering:
    INSERTION at the beginning of the list
    INSERTION at the end of the list
    INSERTION in the middle of the list
    A new interval that merges all existing intervals
    A new interval that overlaps none
    THE case of an empty initial list
