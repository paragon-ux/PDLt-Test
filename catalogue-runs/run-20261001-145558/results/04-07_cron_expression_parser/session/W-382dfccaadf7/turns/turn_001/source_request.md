Implement a cron expression parser and evaluator in Python:
1. Parse standard 5-field cron expressions: minute hour day-of-month month day-of-week.
2. Support: specific values (5), ranges (1-5), steps (*/15, 1-30/5), lists (1,3,5), and wildcard (*).
3. matches(cron_expr, datetime) -> bool: Check if a datetime matches the expression.
4. next_fire(cron_expr, after_datetime) -> datetime: Find the next datetime that matches.
5. Include tests: "*/15 * * * *" fires at :00, :15, :30, :45; "0 9 * * 1-5" fires at 9am on weekdays; "0 0 1 1 *" fires at midnight on January 1st.
