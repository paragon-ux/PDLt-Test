import re

def validate_email(email: str) -> bool:
    """Return True if *email* is a valid email address, False otherwise.

    The validation uses a regular expression that matches most common
    email address formats. It checks for a non‑empty local part, an '@'
    symbol, and a domain part consisting of labels separated by dots.
    """
    # Regular expression pattern for basic email validation.
    # This pattern allows alphanumeric characters and ._%+- in the local part,
    # and ensures the domain part has at least one dot separating labels.
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.fullmatch(pattern, email) is not None
