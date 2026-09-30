READ the 7x7 Latin square grid with cells marked 0 as input
IDENTIFY all cells containing 0
FOR each identified zero cell
ASSIGN a candidate number from 1 to 7 that does not already appear in the cell's row
AND does not already appear in the cell's column
SELECT a candidate that satisfies both row and column constraints
ENDFOR
VERIFY that each row contains each number from 1 to 7 exactly once
VERIFY that each column contains each number from 1 to 7 exactly once
