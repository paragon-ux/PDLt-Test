DEFINE data structures for dancing links nodes and column headers
BUILD the exact cover matrix representing subsets S1 through S9 for universe U
IMPLEMENT dancing links operations
    IMPLEMENT COVER operation to remove a column and its rows
    IMPLEMENT UNCOVER operation to restore a column and its rows
IMPLEMENT recursive search using Algorithm X
    SELECT a column with minimal size
    COVER the selected column
    EXPLORE each row in the column recursively
    UNCOVER the column after recursion
ACCUMULATE each full exact cover solution when all columns are covered
OUTPUT all accumulated solutions in a readable format
CREATE a self-contained test harness
    INVOKE the search routine
    VERIFY each reported solution covers U exactly once without overlap
    VERIFY the test completes successfully
