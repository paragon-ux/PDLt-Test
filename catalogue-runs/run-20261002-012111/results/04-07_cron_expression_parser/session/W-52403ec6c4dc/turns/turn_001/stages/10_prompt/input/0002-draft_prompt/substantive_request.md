TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a cron expression parser and evaluator in Python that can parse standard 5-field cron expressions (minute hour day-of-month month day-of-week). The parser must support specific values (e.g., 5), ranges (e.g., 1-5), steps (e.g., */15, 1-30/5), lists (e.g., 1,3,5), and wildcard (*). Provide a function matches(cron_expr, datetime) -> bool that returns True if a given datetime matches the cron expression. Provide a function next_fire(cron_expr, after_datetime) -> datetime that returns the next datetime after the given after_datetime that satisfies the cron expression. Include tests verifying that the expression "*/15 * * * *" fires at minute :00, :15, :30, and :45; that "0 9 * * 1-5" fires at 9 am on weekdays; and that "0 0 1 1 *" fires at midnight on January 1st.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- matches
- cron_expr
- datetime
- next_fire
- after_datetime
- "*/15 * * * *"
- "0 9 * * 1-5"
- "0 0 1 1 *"
- Python
