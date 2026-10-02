MODEL the protocol as a state machine for the coordinator and participants
    IDENTIFY states for the coordinator
    IDENTIFY states for each participant
    DEFINE transitions based on messages exchanged
ANALYZE deadlock-freeness assuming no message loss and eventual responses
    EVALUATE reachable state combinations
    DETECT cycles with no progress potential
IF deadlock susceptibility under message loss is possible THEN
    DESCRIBE the deadlock scenario
ENDIF
PROVIDE a mitigation such as a timeout-based presumed abort
    SPECIFY timeout thresholds for awaiting responses
    SPECIFY abort actions to be executed upon timeout
