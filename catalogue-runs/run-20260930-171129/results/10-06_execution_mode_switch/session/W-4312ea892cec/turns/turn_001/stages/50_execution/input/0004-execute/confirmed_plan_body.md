VALIDATE that source unit is one of Celsius, Fahrenheit, Kelvin
VALIDATE that target unit is one of Celsius, Fahrenheit, Kelvin
IF source unit equals target unit THEN
RETURN input temperature unchanged
ELSE
CONVERT input temperature to an intermediate Kelvin value using the appropriate formula for the source unit
CONVERT intermediate Kelvin value to the target unit using the appropriate formula for the target unit
RETURN the converted temperature value
ENDIF
IF any unit validation fails THEN
SIGNAL an error indicating unsupported or invalid unit
ENDIF
