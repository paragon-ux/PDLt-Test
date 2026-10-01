PARSE the cron expression string into five field strings
NORMALIZE each field to support specific values, ranges, step values, lists, and wildcards
RESOLVE each normalized field into a concrete set of permitted values for minute, hour, day-of-month, month, and day-of-week
COMPOSE a CronExpression object holding the resolved value sets
DEFINE matches(cron_expr, datetime) to test if the datetime's minute, hour, day-of-month, month, and day-of-week each belong to the corresponding value set and return a boolean
DEFINE next_fire(cron_expr, after_datetime) to advance from after_datetime, evaluating candidates with matches, and return the earliest datetime that satisfies the expression
WRITE unit tests for matches and next_fire that cover the required example expressions
VERIFY that the expression "*/15 * * * *" triggers at minutes 0, 15, 30, and 45 of every hour
VERIFY that the expression "0 9 * * 1-5" triggers at 09:00 on Monday through Friday
VERIFY that the expression "0 0 1 1 *" triggers at 00:00 on January 1st
LIST the operative task entities: matches, next_fire, cron_expr, datetime, after_datetime, minute, hour, day-of-month, month, day-of-week, "*/15 * * * *", "0 9 * * 1-5", "0 0 1 1 *"
