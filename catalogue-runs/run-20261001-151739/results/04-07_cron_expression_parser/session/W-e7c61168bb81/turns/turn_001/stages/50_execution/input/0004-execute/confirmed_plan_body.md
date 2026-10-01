PARSE the cron expression into the five fields (minute, hour, day-of-month, month, day-of-week)
NORMALIZE each field token into a set of allowed integer values according to cron syntax (wildcard, list, range, step)
VALIDATE that all normalized values respect the legal ranges for each field
DEFINE function matches(cron_expr, datetime) -> bool
    PARSE and NORMALIZE the cron expression
    EXTRACT minute, hour, day-of-month, month, day-of-week from the datetime argument
    COMPARE each datetime component to its corresponding normalized set
    RETURN true if all components match, otherwise false
DEFINE function next_fire(cron_expr, after_datetime) -> datetime
    SET candidate to after_datetime plus one minute
    REPEAT
        IF matches(cron_expr, candidate) THEN
            RETURN candidate
        INCREMENT candidate by one minute
    END REPEAT
DEVELOP unit test suite for the parser and evaluator
    FOR expression "*/15 * * * *"
        CREATE test cases at minutes :00, :15, :30, :45 of several hours and ASSERT matches returns true
        CREATE test cases at minutes not divisible by 15 and ASSERT matches returns false
    FOR expression "0 9 * * 1-5"
        CREATE test cases at 9:00 on Monday through Friday and ASSERT matches returns true
        CREATE test cases on Saturday, Sunday, or at other times and ASSERT matches returns false
    FOR expression "0 0 1 1 *"
        CREATE test cases at midnight on January 1st of multiple years and ASSERT matches returns true
        CREATE test cases at other dates and times and ASSERT matches returns false
PACKAGE the implementation and test suite as a Python module
PROVIDE documentation that describes usage of matches and next_fire functions with example calls
