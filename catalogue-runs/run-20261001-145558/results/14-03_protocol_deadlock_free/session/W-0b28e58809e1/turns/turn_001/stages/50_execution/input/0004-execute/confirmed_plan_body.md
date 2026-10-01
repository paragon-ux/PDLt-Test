DEFINE state machine for coordinator with states START, PREPARE, COMMIT, ABORT, DONE
DEFINE state machine for participant with states IDLE, PREPARED, COMMITTED, ABORTED
SPECIFY coordinator transitions: FROM START TO PREPARE SEND prepare request to all participants; FROM PREPARE TO COMMIT IF all votes YES SEND commit request; FROM PREPARE TO ABORT IF any vote NO SEND abort request; FROM COMMIT TO DONE FINALIZE; FROM ABORT TO DONE FINALIZE
SPECIFY participant transitions: FROM IDLE TO PREPARED ON receive prepare request SEND vote YES OR NO; FROM PREPARED TO COMMITTED ON receive commit request; FROM PREPARED TO ABORTED ON receive abort request
ANALYZE deadlock‑free property assuming no message loss and eventual responses
ASSERT deadlock‑free under these assumptions
DESCRIBE scenario with message loss where a participant misses commit or abort decision
IDENTIFY potential deadlock where coordinator awaits missing votes and participants await missing final decision
PROPOSE mitigation using timeout‑based presumed abort: IF coordinator timeout without all votes THEN ABORT transaction; IF participant timeout without final decision THEN ABORT locally
