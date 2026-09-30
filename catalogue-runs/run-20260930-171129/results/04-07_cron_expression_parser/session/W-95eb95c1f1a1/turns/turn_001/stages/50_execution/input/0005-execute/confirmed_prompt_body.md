READ cron expression string as cron_expr
PARSE the 5 fields (minute, hour, day-of-month, month, day-of-week) supporting specific values, ranges, steps, lists, wildcard
DEFINE FUNCTION matches(cron_expr, datetime) RETURN boolean indicating if datetime matches the expression
DEFINE FUNCTION next_fire(cron_expr, after_datetime) RETURN the next datetime after after_datetime that matches the expression
INCLUDE tests:
VERIFY that matches for "*/15 * * * *" is true at minutes 0, 15, 30, 45 of any hour
VERIFY that matches for "0 9 * * 1-5" is true at 9:00 on weekdays
VERIFY that matches for "0 0 1 1 *" is true at midnight on January 1st
