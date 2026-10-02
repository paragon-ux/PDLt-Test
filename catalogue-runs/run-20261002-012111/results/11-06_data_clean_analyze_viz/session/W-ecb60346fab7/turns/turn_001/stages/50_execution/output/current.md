import csv
import json
import math
import statistics
from datetime import datetime

# Input CSV data as a multi-line string (would be read from a file in a real scenario)
csv_data = """Name,Age,Salary,Department,Start Date
Alice,30,75000,Engineering,2020-01-15
Bob,,85000,Engineering,2019-06-01
Charlie,28,,Marketing,2021-03-10
Diana,35,92000,Engineering,2018-11-20
Eve,42,78000,,2017-05-30
Frank,29,71000,Marketing,invalid-date
Grace,31,88000,Engineering,2020-08-12
Hank,27,65000,Marketing,2022-01-05
Ivy,,95000,Engineering,2019-09-15
Jack,33,82000,Sales,2020-04-22
,25,70000,Sales,2021-07-18
Leo,38,91000,Engineering,2018-03-01
"""

reference_date = datetime(2026, 9, 28)

# Helper functions
def parse_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def parse_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

# Load CSV
records = []
reader = csv.DictReader(csv_data.splitlines())
for row in reader:
    # Clean and validate fields
    name = row["Name"].strip() or None
    age = parse_int(row["Age"].strip())
    salary = parse_float(row["Salary"].strip())
    department = row["Department"].strip() or None
    start_date = parse_date(row["Start Date"].strip())

    # Flag rows with critical missing data (Name, Department, Start Date, Salary)
    if not name or not department or not start_date or salary is None:
        # For this pipeline we drop rows missing any of those required fields
        continue

    records.append({
        "Name": name,
        "Age": age,
        "Salary": salary,
        "Department": department,
        "Start Date": start_date,
    })

# Compute tenure for each employee
for rec in records:
    tenure_days = (reference_date - rec["Start Date"]).days
    rec["Tenure Years"] = round(tenure_days / 365.25, 2)

# Aggregate per-department statistics
dept_stats = {}
for rec in records:
    dept = rec["Department"]
    if dept not in dept_stats:
        dept_stats[dept] = {
            "salaries": [],
            "count": 0,
        }
    dept_stats[dept]["salaries"].append(rec["Salary"])
    dept_stats[dept]["count"] += 1

summary_table = []
bar_chart_data = []
for dept, data in dept_stats.items():
    salaries = data["salaries"]
    count = data["count"]
    mean_salary = round(statistics.mean(salaries), 2)
    median_salary = round(statistics.median(salaries), 2)
    stddev_salary = round(statistics.pstdev(salaries), 2)  # population std dev
    summary_table.append({
        "Department": dept,
        "Count": count,
        "Mean Salary": mean_salary,
        "Median Salary": median_salary,
        "Salary StdDev": stddev_salary,
    })
    bar_chart_data.append({"Department": dept, "Average Salary": mean_salary})

# Output results as JSON for easy consumption
output = {
    "cleaned_summary_table": summary_table,
    "bar_chart_dataset": bar_chart_data,
    "employee_records": records,
}
print(json.dumps(output, indent=2))
