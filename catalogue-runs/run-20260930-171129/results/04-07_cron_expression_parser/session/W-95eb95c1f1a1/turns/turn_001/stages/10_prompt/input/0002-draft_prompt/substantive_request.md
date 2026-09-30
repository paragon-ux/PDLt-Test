TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a cron expression parser and evaluator in Python with the following capabilities: parse standard 5-field cron expressions (minute, hour, day-of-month, month, day-of-week); support specific values, ranges, steps, lists, and wildcard; provide a function matches(cron_expr, datetime) that returns a boolean indicating if a given datetime matches the expression; provide a function next_fire(cron_expr, after_datetime) that returns the next datetime matching the expression; include tests demonstrating that "*/15 * * * *" fires at minute 0, 15, 30, 45; "0 9 * * 1-5" fires at 9am on weekdays; and "0 0 1 1 *" fires at midnight on January 1st.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- matches
- next_fire
- cron_expr
- datetime
