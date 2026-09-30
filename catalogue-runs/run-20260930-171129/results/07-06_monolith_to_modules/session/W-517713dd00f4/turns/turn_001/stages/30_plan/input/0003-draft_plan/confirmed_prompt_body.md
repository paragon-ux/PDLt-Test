READ the single-file Python script that processes CSV files
PARTITION the script functionality into the following modules of the package 'mypackage':
- __init__.py
- io.py (handle CSV file reading and writing)
- validation.py (perform data validation checks)
- transform.py (apply transformation logic to the data)
- report.py (generate summary reports or outputs)
ORGANIZE each extracted function or class into the appropriate module based on its responsibility
CREATE a tests/ directory with unit test files for each module (test_io.py, test_validation.py, test_transform.py, test_report.py) ensuring coverage of core behaviors
ENSURE the package is importable and includes a setup.cfg or pyproject.toml for packaging metadata
