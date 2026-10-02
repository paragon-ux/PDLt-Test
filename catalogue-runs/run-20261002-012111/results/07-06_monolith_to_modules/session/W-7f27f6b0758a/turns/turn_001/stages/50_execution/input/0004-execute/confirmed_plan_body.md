READ the supplied Python script that processes CSV files.
EXTRACT the core functionalities: CSV reading, row validation, data transformation, numeric summarization, JSON report generation.
CREATE the package directory mypackage.
CREATE the module mypackage/__init__.py.
CREATE the module mypackage/io.py.
DEFINE function read_csv in mypackage/io.py to replicate the extracted CSV reading logic.
IMPORT csv, sys in mypackage/io.py.
CREATE the module mypackage/validation.py.
DEFINE function validate_row in mypackage/validation.py to replicate the extracted validation rules.
IMPORT any required modules in mypackage/validation.py.
CREATE the module mypackage/transform.py.
DEFINE function transform in mypackage/transform.py to replicate the extracted transformation steps.
IMPORT any required modules in mypackage/transform.py.
CREATE the module mypackage/report.py.
DEFINE function summarize in mypackage/report.py to replicate the extracted summarization logic using json, statistics, datetime.
DEFINE function write_report in mypackage/report.py to output the JSON report using json, statistics, datetime.
IMPORT json, statistics, datetime in mypackage/report.py.
INCLUDE unit tests for each module covering read_csv, validate_row, transform, summarize, write_report.
ENSURE the package behavior matches the original script's functionality.
