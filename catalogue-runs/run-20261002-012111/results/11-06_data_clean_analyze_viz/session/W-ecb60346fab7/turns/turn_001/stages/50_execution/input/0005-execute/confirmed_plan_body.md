LOAD the CSV file with columns Name, Age, Salary, Department, Start Date
HANDLE missing or invalid values by filling, dropping, or flagging as appropriate
GROUP records BY Department
FOR each Department
    CALCULATE count of records
    CALCULATE mean salary
    CALCULATE median salary
    CALCULATE salary standard deviation
ENDFOR
CALCULATE each employee's tenure in years as the difference between Start Date and reference date 2026-09-28
COMPOSE a cleaned summary table with per-department statistics and tenure information
PREPARE a dataset for a bar chart showing average salary by department
OUTPUT the cleaned summary table
OUTPUT the bar chart dataset
