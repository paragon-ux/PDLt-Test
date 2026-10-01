READ the request to implement a cron expression parser and evaluator in Python
DEFINE a function matches(cron_expr, datetime) that returns a boolean indicating if the datetime matches the cron expression
DEFINE a function next_fire(cron_expr, after_datetime) that returns the next datetime after after_datetime that matches the cron expression
SUPPORT parsing of standard 5-field cron expressions (minute, hour, day-of-month, month, day-of-week) including specific values, ranges, steps, lists, and wildcards
ENSURE the parser correctly interprets fields according to cron syntax rules
INCLUDE tests verifying that "*/15 * * * *" fires at quarter-hour intervals
INCLUDE tests verifying that "0 9 * * 1-5" fires at 09:00 on weekdays (Monday through Friday)
INCLUDE tests verifying that "0 0 1 1 *" fires at midnight on January 1st
OUTPUT the Python code for the parser, the two functions, and the test suite
