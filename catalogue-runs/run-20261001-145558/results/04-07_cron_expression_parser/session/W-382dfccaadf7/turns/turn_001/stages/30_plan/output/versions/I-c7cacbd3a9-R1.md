READ the request to implement a cron expression parser and evaluator in Python
DEFINE a parser for standard 5‑field cron expressions handling values, ranges, steps, lists, and wildcards
IMPLEMENT function matches(cron_expr, datetime) that returns a boolean indicating if the datetime matches the parsed cron expression
IMPLEMENT function next_fire(cron_expr, after_datetime) that computes the next datetime after after_datetime that matches the cron expression using the parser and matching logic
WRITE a test suite that includes:
    VERIFY that "*/15 * * * *" fires at quarter‑hour intervals
    VERIFY that "0 9 * * 1-5" fires at 09:00 on weekdays (Monday through Friday)
    VERIFY that "0 0 1 1 *" fires at midnight on January 1st
