TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Create a data processing pipeline for the provided CSV containing columns Name, Age, Salary, Department, and Start Date. The pipeline must load the CSV, handle missing or invalid values (by filling, dropping, or flagging as appropriate), compute per-department statistics: count of records, mean salary, median salary, and salary standard deviation. It must also calculate each employee's tenure in years from their Start Date to the reference date 2026-09-28. Finally, output a cleaned summary table and a dataset suitable for a bar chart showing average salary by department.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Name
- Age
- Salary
- Department
- Start Date
- 2026-09-28
