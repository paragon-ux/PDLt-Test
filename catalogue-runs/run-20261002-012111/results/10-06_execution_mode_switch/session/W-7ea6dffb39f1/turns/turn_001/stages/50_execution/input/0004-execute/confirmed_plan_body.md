READ numeric temperature value as temperature
READ source temperature scale as source_scale
READ target temperature scale as target_scale
IF source_scale EQUALS target_scale THEN
    RETURN temperature
ELSE
    CONVERT temperature FROM source_scale TO target_scale
    RETURN converted temperature
ENDIF
