DEFINE a function with parameters: input temperature value, source unit, target unit
VALIDATE that source and target units are among Celsius, Fahrenheit, Kelvin
IF source unit equals target unit THEN RETURN the input temperature unchanged
ELSE DETERMINE the conversion pathway:
IF converting from Celsius to Fahrenheit THEN APPLY (value * 9/5) + 32
IF converting from Celsius to Kelvin THEN APPLY value + 273.15
IF converting from Fahrenheit to Celsius THEN APPLY (value - 32) * 5/9
IF converting from Fahrenheit to Kelvin THEN APPLY ((value - 32) * 5/9) + 273.15
IF converting from Kelvin to Celsius THEN APPLY value - 273.15
IF converting from Kelvin to Fahrenheit THEN APPLY ((value - 273.15) * 9/5) + 32
RETURN the computed temperature value
