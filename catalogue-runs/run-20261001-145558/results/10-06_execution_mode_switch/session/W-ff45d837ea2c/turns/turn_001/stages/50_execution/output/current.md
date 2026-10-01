def convert_temperature(value, source_scale):
    """Convert a temperature to the other two scales.

    Parameters:
        value (float or int): The numeric temperature value.
        source_scale (str): The scale of the input value. Must be one of
            "Celsius", "Fahrenheit", or "Kelvin" (case‑insensitive).

    Returns:
        dict: A mapping of the two target scales to their converted values
            with unit labels, e.g. {"Fahrenheit": "98.6°F", "Kelvin": "310.15K"}.
    """
    # Validate numeric input
    if not isinstance(value, (int, float)):
        raise TypeError("Temperature value must be a numeric type")

    # Normalise source scale string
    scale = source_scale.strip().lower()
    if scale not in {"celsius", "fahrenheit", "kelvin"}:
        raise ValueError("source_scale must be 'Celsius', 'Fahrenheit', or 'Kelvin'")

    # Helper conversions
    def c_to_f(c):
        return c * 9 / 5 + 32

    def c_to_k(c):
        return c + 273.15

    def f_to_c(f):
        return (f - 32) * 5 / 9

    def k_to_c(k):
        return k - 273.15

    # Compute conversions based on source scale
    if scale == "celsius":
        c = float(value)
        f = c_to_f(c)
        k = c_to_k(c)
        result = {"Fahrenheit": f"{f:.2f}°F", "Kelvin": f"{k:.2f}K"}
    elif scale == "fahrenheit":
        f = float(value)
        c = f_to_c(f)
        k = c_to_k(c)
        result = {"Celsius": f"{c:.2f}°C", "Kelvin": f"{k:.2f}K"}
    else:  # kelvin
        k = float(value)
        c = k_to_c(k)
        f = c_to_f(c)
        result = {"Celsius": f"{c:.2f}°C", "Fahrenheit": f"{f:.2f}°F"}

    return result
