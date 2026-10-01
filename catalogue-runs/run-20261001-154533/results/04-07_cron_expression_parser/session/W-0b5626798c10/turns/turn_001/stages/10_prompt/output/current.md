IMPLEMENT a Python module that parses standard 5-field cron expressions (minute, hour, day-of-month, month, day-of-week) and evaluates them.
SUPPORT specific values (e.g., 5), ranges (e.g., 1-5), step values (e.g., */15, 1-30/5), lists (e.g., 1,3,5), and wildcards (*).
PROVIDE a function matches(cron_expr, datetime) -> bool that returns True if a given datetime matches the expression.
PROVIDE a function next_fire(cron_expr, after_datetime) -> datetime that returns the next datetime after after_datetime that matches the expression.
INCLUDE tests verifying that the expression "*/15 * * * *" fires at minute 0, 15, 30, 45 of each hour.
INCLUDE tests verifying that the expression "0 9 * * 1-5" fires at 9:00 on weekdays.
INCLUDE tests verifying that the expression "0 0 1 1 *" fires at midnight on January 1st.
LIST the operative task entities: matches, next_fire, cron_expr, datetime, after_datetime, */15 * * * *, 0 9 * * 1-5, 0 0 1 1 *, minute, hour, day-of-month, month, day-of-week.
