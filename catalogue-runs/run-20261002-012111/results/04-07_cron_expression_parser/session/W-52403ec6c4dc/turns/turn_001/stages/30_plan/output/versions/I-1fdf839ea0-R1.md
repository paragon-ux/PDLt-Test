DESIGN parser for 5-field cron expressions supporting specific values, ranges, steps, lists, and wildcard
IMPLEMENT function to split a cron expression into its five fields
TRANSLATE each field into a normalized representation of allowed values
VALIDATE parsed fields for syntactic correctness
IMPLEMENT matches(cron_expr, datetime) to:
    PARSE the cron expression
    COMPARE each datetime component against the corresponding allowed values
    RETURN true if all components satisfy constraints
IMPLEMENT next_fire(cron_expr, after_datetime) to:
    PARSE the cron expression
    ITERATIVELY advance from after_datetime to the next datetime that satisfies matches
    RETURN the discovered datetime
DEVELOP unit tests that:
    VERIFY that "*/15 * * * *" matches minutes 0, 15, 30, and 45 of any hour
    VERIFY that "0 9 * * 1-5" matches 9:00 on weekdays
    VERIFY that "0 0 1 1 *" matches midnight on January 1
EXECUTE the unit tests and ensure all pass
DOCUMENT the public API and provide usage examples
