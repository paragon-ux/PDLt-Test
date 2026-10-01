CREATE package directory mypackage
CREATE __init__.py file importing the public interfaces of the package
CREATE io.py file defining functions to read and write CSV files
CREATE validation.py file defining functions to perform data validation
CREATE transform.py file defining functions to apply data transformations
CREATE report.py file defining functions to generate reports
WRITE unit test file test_io.py covering the io module functionality
WRITE unit test file test_validation.py covering the validation module functionality
WRITE unit test file test_transform.py covering the transform module functionality
WRITE unit test file test_report.py covering the report module functionality
ARRANGE test suite to discover and run all unit tests
