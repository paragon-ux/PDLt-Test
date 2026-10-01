DEFINE the two-phase commit protocol as a state machine for the coordinator and each participant
DEFINE states for the coordinator: START, PREPARE, COMMIT, ABORT, DONE
DEFINE states for a participant: IDLE, PREPARED, COMMITTED, ABORTED
DEFINE transitions for the coordinator: FROM START TO PREPARE SEND prepare request to all participants; FROM PREPARE TO COMMIT IF all participants vote YES SEND commit request; FROM PREPARE TO ABORT IF any participant votes NO SEND abort request; FROM COMMIT TO DONE finalize; FROM ABORT TO DONE finalize
DEFINE transitions for a participant: FROM IDLE TO PREPARED ON receive prepare request SEND vote YES (or NO) to coordinator; FROM PREPARED TO COMMITTED ON receive commit request; FROM PREPARED TO ABORTED ON receive abort request
ANALYZE deadlock‑free property assuming no message loss and all participants eventually respond
ASSERT the protocol is deadlock‑free under these assumptions
CONSIDER scenario with message loss where a participant does not receive the commit or abort decision
DESCRIBE potential deadlock where coordinator waits for responses that never arrive and participants wait for final decision
PROPOSE mitigation using timeout‑based presumed abort: IF coordinator does not receive all votes within timeout THEN abort transaction; IF participant does not receive final decision within timeout THEN abort locally
