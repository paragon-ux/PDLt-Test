def convert_temperature(value, source_unit, target_unit):
    """Convert temperature between Celsius, Fahrenheit, and Kelvin.

    Args:
        value (float): Numeric temperature value.
        source_unit (str): "Celsius", "Fahrenheit", or "Kelvin" (case‑insensitive).
        target_unit (str): "Celsius", "Fahrenheit", or "Kelvin" (case‑insensitive).

    Returns:
        float: Converted temperature.

    Raises:
        ValueError: If an unsupported unit is supplied.
    """
    # Normalise unit strings
    src = source_unit.strip().lower()
    tgt = target_unit.strip().lower()
    valid = {"celsius", "fahrenheit", "kelvin"}
    if src not in valid or tgt not in valid:
        raise ValueError("Unsupported temperature unit")

    # If source and target are the same, return the original value
    if src == tgt:
        return value

    # Convert source to Kelvin as an intermediate step
    if src == "celsius":
        kelvin = value + 273.15
    elif src == "fahrenheit":
        kelvin = (value - 32) * 5/9 + 273.15
    else:  # src == "kelvin"
        kelvin = value

    # Convert Kelvin to target unit
    if tgt == "celsius":
        return kelvin - 273.15
    elif tgt == "fahrenheit":
        return (kelvin - 273.15) * 9/5 + 32
    else:  # tgt == "kelvin"
        return kelvin
