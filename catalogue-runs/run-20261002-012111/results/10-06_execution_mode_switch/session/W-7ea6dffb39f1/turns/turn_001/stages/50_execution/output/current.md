def convert_temperature(temperature, source_scale, target_scale):
    """Convert a temperature between Celsius, Fahrenheit, and Kelvin.

    Args:
        temperature (float): The numeric temperature value.
        source_scale (str): The scale of the input temperature. Must be one of
            "Celsius", "Fahrenheit", or "Kelvin" (case‑insensitive).
        target_scale (str): The desired output scale. Same allowed values as
            ``source_scale``.

    Returns:
        float: The temperature expressed in the target scale.
    """
    # Normalise scale identifiers
    src = source_scale.strip().lower()
    tgt = target_scale.strip().lower()

    # If the scales are the same, return the original temperature
    if src == tgt:
        return temperature

    # Convert the source temperature to Celsius as an intermediate step
    if src == "celsius":
        celsius = temperature
    elif src == "fahrenheit":
        celsius = (temperature - 32) * 5 / 9
    elif src == "kelvin":
        celsius = temperature - 273.15
    else:
        raise ValueError(f"Unsupported source scale: {source_scale}")

    # Convert from Celsius to the target scale
    if tgt == "celsius":
        return celsius
    elif tgt == "fahrenheit":
        return celsius * 9 / 5 + 32
    elif tgt == "kelvin":
        return celsius + 273.15
    else:
        raise ValueError(f"Unsupported target scale: {target_scale}")
