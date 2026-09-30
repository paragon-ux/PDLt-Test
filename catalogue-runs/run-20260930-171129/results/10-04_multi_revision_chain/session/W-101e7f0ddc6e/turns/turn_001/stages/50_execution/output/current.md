import re

def is_valid_email(email: str) -> bool:
    """Validate an email address using a regular expression.

    Returns True if *email* matches the pattern, otherwise False.
    """
    # Simple email regex covering most common cases
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.fullmatch(pattern, email) is not None
