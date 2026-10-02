READ the numeric temperature value as temperature
READ the source temperature scale as source_scale (Celsius, Fahrenheit, Kelvin)
READ the target temperature scale as target_scale (Celsius, Fahrenheit, Kelvin)
IF source_scale EQUALS target_scale THEN
    RETURN temperature
ELSE
    CONVERT temperature FROM source_scale TO target_scale
    RETURN the converted temperature
ENDIF
