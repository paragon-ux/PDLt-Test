ANALYZE the request and constraints
SELECT a suitable programming language for concise illustration
DEFINE function signature accepting a sorted list of non-overlapping intervals and a new interval
SPECIFY interval representation as two-element tuples (start, end)
DESIGN a linear-time algorithm
    INITIALIZE an empty result list
    ITERATE through the original intervals in order
    IF current interval ends before new interval starts THEN APPEND current interval to result
    ELSE IF current interval starts after new interval ends THEN
        IF new interval not yet added THEN APPEND new interval to result
        APPEND current interval and CONTINUE
    ELSE MERGE current interval with new interval by expanding new interval's start and end
    ENDIF
    CONTINUE iteration
    AFTER loop, IF new interval not yet added THEN APPEND it
IMPLEMENT the algorithm using a single FOR loop and conditional logic
WRITE the function body following the designed steps
CREATE a test suite
    FOR each required scenario (insertion at the beginning, insertion at the end, insertion in the middle, insertion merging all intervals, insertion overlapping none, insertion when the initial list is empty)
        SPECIFY input intervals, new interval, expected output
        ADD a test case invoking the function and asserting equality
RUN the test suite and produce a summary of pass/fail results
COMBINE the function definition and test suite into one source artifact
OUTPUT the complete code and tests as the final deliverable
