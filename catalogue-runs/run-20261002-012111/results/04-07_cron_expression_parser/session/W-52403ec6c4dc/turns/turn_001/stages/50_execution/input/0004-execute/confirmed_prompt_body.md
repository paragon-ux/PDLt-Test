IMPLEMENT a cron expression parser and evaluator in Python that parses standard 5-field cron expressions (minute hour day-of-month month day-of-week).
SUPPORT specific values (e.g., 5), ranges (e.g., 1-5), steps (e.g., */15, 1-30/5), lists (e.g., 1,3,5), and wildcard (*).
PROVIDE the function matches(cron_expr, datetime) -> bool that returns True if a given datetime matches the cron expression.
PROVIDE the function next_fire(cron_expr, after_datetime) -> datetime that returns the next datetime after the given after_datetime that satisfies the cron expression.
INCLUDE tests verifying that the expression "*/15 * * * *" fires at minute :00, :15, :30, and :45; that the expression "0 9 * * 1-5" fires at 9 am on weekdays; and that the expression "0 0 1 1 *" fires at midnight on January 1st.
