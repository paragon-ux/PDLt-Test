READ the supplied single-file Python script that processes CSV files, validates rows, transforms data, summarizes numeric fields, and writes a JSON report.
CREATE the package mypackage.
CREATE the module mypackage/__init__.py.
CREATE the module mypackage/io.py.
DEFINE function read_csv in mypackage/io.py that uses csv and sys.
CREATE the module mypackage/validation.py.
DEFINE function validate_row in mypackage/validation.py.
CREATE the module mypackage/transform.py.
DEFINE function transform in mypackage/transform.py.
CREATE the module mypackage/report.py.
DEFINE function summarize in mypackage/report.py that uses json, statistics, datetime.
DEFINE function write_report in mypackage/report.py that uses json, statistics, datetime.
IMPORT csv, sys, json, statistics, datetime in appropriate modules to preserve original functionality.
INCLUDE unit tests for each module covering read_csv, validate_row, transform, summarize, write_report.
ENSURE the package behavior matches the original script's functionality.
