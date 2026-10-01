TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Prove that the invariant "At most one direction has a non-RED light at any time" is preserved by all transitions of the traffic light controller state machine. The state machine has states RED, GREEN, YELLOW with transitions: RED -> GREEN after 60 seconds, GREEN -> YELLOW after 45 seconds, YELLOW -> RED after 5 seconds. There are two crossing directions, each with its own identical state machine; direction B starts in RED and only transitions to GREEN when direction A enters RED. Use induction on the number of transitions taken and identify any necessary assumptions for the proof.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- RED
- GREEN
- YELLOW
- 60 seconds
- 45 seconds
- 5 seconds
- At most one direction has a non-RED light at any time
- direction A
- direction B
