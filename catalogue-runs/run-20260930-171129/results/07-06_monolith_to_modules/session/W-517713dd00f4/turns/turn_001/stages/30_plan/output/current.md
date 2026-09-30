READ the single-file Python script that processes CSV files
EXTRACT each function or class from the script
CREATE package directory 'mypackage'
CREATE module mypackage/__init__.py
CREATE module mypackage/io.py
CREATE module mypackage/validation.py
CREATE module mypackage/transform.py
CREATE module mypackage/report.py
ASSIGN each extracted function or class to the appropriate module based on its responsibility (CSV I/O to io.py, validation checks to validation.py, transformation logic to transform.py, report generation to report.py)
WRITE import statements in mypackage/__init__.py to expose public symbols
CREATE a tests/ directory at the project root
CREATE test file tests/test_io.py covering core I/O behaviors
CREATE test file tests/test_validation.py covering validation checks
CREATE test file tests/test_transform.py covering transformation logic
CREATE test file tests/test_report.py covering report generation
ENSURE each test imports the corresponding module from mypackage and asserts expected outcomes
ADD a packaging metadata file (setup.cfg or pyproject.toml) with package name, version, and required metadata
VERIFY that the package can be imported without errors
