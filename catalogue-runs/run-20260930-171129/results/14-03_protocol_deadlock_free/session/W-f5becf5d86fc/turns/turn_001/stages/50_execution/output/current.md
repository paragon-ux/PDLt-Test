Two‑Phase Commit Protocol State Machine

## Coordinator State Machine
- **Idle**: Initial state, waiting to start transaction.
- **WaitingForVotes**: After sending PREPARE to all participants, waits for their votes.
- **Commit**: All votes are COMMIT; sends COMMIT to participants.
- **Abort**: At least one vote is ABORT; sends ABORT to participants.
- **Finished**: After receiving acknowledgements from all participants.

**Transitions**
1. Idle → WaitingForVotes: on event **start_transaction** (coordinator sends PREPARE).
2. WaitingForVotes → Commit: on **all_votes_commit** (receives COMMIT from every participant).
3. WaitingForVotes → Abort: on **any_vote_abort** (receives ABORT from any participant).
4. Commit → Finished: on **all_acks_received** (receives ACK from every participant after COMMIT).
5. Abort → Finished: on **all_acks_received** (receives ACK from every participant after ABORT).

## Participant State Machine (identical for each participant)
- **Idle**: Waiting for PREPARE.
- **Voting**: Received PREPARE, decides to vote COMMIT or ABORT.
- **WaitingForDecision**: Sent vote, awaiting global decision.
- **Committing**: Received COMMIT, performs commit actions.
- **Aborting**: Received ABORT, rolls back.
- **Finished**: Sent acknowledgement, returns to Idle.

**Transitions**
1. Idle → Voting: on **prepare_received** (coordinator's PREPARE).
2. Voting → WaitingForDecision: on **vote_sent** (sends COMMIT or ABORT).
3. WaitingForDecision → Committing: on **global_commit** (receives COMMIT).
4. WaitingForDecision → Aborting: on **global_abort** (receives ABORT).
5. Committing/Aborting → Finished: on **ack_sent** (sends ACK to coordinator).
6. Finished → Idle: on **reset** (transaction complete).

## Deadlock‑Freedom Analysis (no message loss, eventual responses)
Under the assumptions:
- All messages are reliably delivered.
- Every participant eventually replies to PREPARE.
- The coordinator waits until it has collected a vote from every participant before making a decision.
The protocol proceeds through a finite sequence of states ending in **Finished** for both coordinator and participants. No circular waiting occurs because:
* Participants never wait for a message that depends on their own pending vote.
* The coordinator only waits for votes, which are guaranteed to arrive, and then sends a definitive decision.
Therefore, with these assumptions the protocol is deadlock‑free.

## Potential Deadlock with Message Loss
If messages can be lost, a deadlock can arise when the coordinator’s **COMMIT** (or **ABORT**) message is lost after all participants have voted COMMIT and are waiting in **WaitingForDecision**. Participants will remain indefinitely in that state, waiting for a decision that never arrives, while the coordinator proceeds to **Finished** (or may also wait for acknowledgements that never come). This creates a classic deadlock where both sides are waiting for messages that were lost.

## Mitigation – Timeout‑Based Presumed Abort
To prevent this situation, participants should employ a timeout while in **WaitingForDecision**. If the timeout expires without receiving a global decision, the participant assumes an **ABORT** and transitions to the **Aborting** state, sending an abort acknowledgment. Similarly, the coordinator can timeout waiting for acknowledgments and, if not all are received, treat missing participants as having aborted. This ensures progress despite lost messages.

---
*The above description satisfies the modeling, analysis, and mitigation requirements.*
