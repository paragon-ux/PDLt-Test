OPERATIVE TASK ENTITIES:
- Name
- Age
- Salary
- Department
- Start Date
- 2026-09-28

LOAD the CSV containing columns Name, Age, Salary, Department, and Start Date.
HANDLE missing or invalid values by filling, dropping, or flagging as appropriate.
COMPUTE per-department statistics:
    FOR each Department:
        CALCULATE count of records.
        CALCULATE mean salary.
        CALCULATE median salary.
        CALCULATE salary standard deviation.
CALCULATE each employee's tenure in years from Start Date to reference date 2026-09-28.
OUTPUT a cleaned summary table.
OUTPUT a dataset suitable for a bar chart showing average salary by department.
