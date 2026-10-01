IMPLEMENT a cron expression parser and evaluator in Python that parses standard 5-field cron expressions (minute, hour, day-of-month, month, day-of-week) and supports specific values, ranges, steps, lists, and wildcard.
DEFINE the function matches(cron_expr, datetime) -> bool that checks if a datetime matches the expression.
DEFINE the function next_fire(cron_expr, after_datetime) -> datetime that finds the next datetime that matches the expression.
INCLUDE tests for the expression "*/15 * * * *" verifying it fires at minutes :00, :15, :30, and :45 each hour.
INCLUDE tests for the expression "0 9 * * 1-5" verifying it fires at 9:00 AM on weekdays (Monday through Friday).
INCLUDE tests for the expression "0 0 1 1 *" verifying it fires at midnight on January 1st.
