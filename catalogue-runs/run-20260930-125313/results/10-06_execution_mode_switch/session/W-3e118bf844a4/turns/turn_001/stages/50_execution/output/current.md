def convert_temperature(value, source_unit, target_unit):
    """Convert temperature between Celsius, Fahrenheit, and Kelvin.

    Parameters:
        value (float): Temperature value to convert.
        source_unit (str): Unit of the input temperature. Must be 'C', 'F', or 'K'.
        target_unit (str): Desired unit for output temperature. Must be 'C', 'F', or 'K'.

    Returns:
        float: Converted temperature value.
    """
    source = source_unit.upper()
    target = target_unit.upper()
    if source not in {'C', 'F', 'K'} or target not in {'C', 'F', 'K'}:
        raise ValueError('source and target units must be one of C, F, K')
    if source == target:
        return value
    # Convert source to Celsius first
    if source == 'C':
        celsius = value
    elif source == 'F':
        celsius = (value - 32) * 5/9
    else:  # source == 'K'
        celsius = value - 273.15
    # Convert Celsius to target
    if target == 'C':
        return celsius
    elif target == 'F':
        return (celsius * 9/5) + 32
    else:  # target == 'K'
        return celsius + 273.15

# Example usage:
# print(convert_temperature(0, 'C', 'F'))  # 32.0
