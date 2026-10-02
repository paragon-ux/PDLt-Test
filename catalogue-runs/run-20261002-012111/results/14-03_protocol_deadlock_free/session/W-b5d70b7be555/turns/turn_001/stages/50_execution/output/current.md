**State Machine Model**

**Coordinator States**
1. **Idle** – waiting to start a transaction.
2. **WaitingForVotes** – after sending PREPARE to all participants, awaiting their votes.
3. **CommitPhase** – after receiving all COMMIT votes, sending COMMIT to all participants.
4. **AbortPhase** – after receiving any ABORT vote, sending ABORT to all participants.
5. **Finished** – transaction completed (either committed or aborted).

**Participant States** (each participant follows the same state machine)
1. **Idle** – waiting for a PREPARE message.
2. **Deciding** – after receiving PREPARE, deciding to vote COMMIT or ABORT.
3. **WaitingForDecision** – after sending its vote, waiting for the coordinator’s final decision (COMMIT or ABORT).
4. **Committed** – after receiving COMMIT, applying changes and acknowledging.
5. **Aborted** – after receiving ABORT, discarding changes and acknowledging.

**Transitions (Coordinator)**
- *Idle → WaitingForVotes*: on `start_transaction`, send PREPARE to all participants.
- *WaitingForVotes → CommitPhase*: on receiving COMMIT vote from every participant, send COMMIT to all.
- *WaitingForVotes → AbortPhase*: on receiving ABORT vote from any participant, send ABORT to all.
- *CommitPhase → Finished*: after sending COMMIT (participants will acknowledge, but coordinator may consider the transaction finished immediately).
- *AbortPhase → Finished*: after sending ABORT.

**Transitions (Participant)**
- *Idle → Deciding*: on receiving PREPARE from coordinator.
- *Deciding → WaitingForDecision*: after sending vote (COMMIT or ABORT) to coordinator.
- *WaitingForDecision → Committed*: on receiving COMMIT from coordinator.
- *WaitingForDecision → Aborted*: on receiving ABORT from coordinator.

**Deadlock‑Free Analysis (No Message Loss, All Respond)**
Under the given assumptions, every sent message is eventually delivered and every participant eventually sends its vote. The reachable state space consists of:
- Coordinator in *WaitingForVotes* with any subset of participants having voted COMMIT and the rest still in *Deciding*.
- Once the coordinator receives all votes, it deterministically moves to either *CommitPhase* or *AbortPhase* and terminates.
- Participants, after voting, wait in *WaitingForDecision* and will receive the final decision because the coordinator will always send it.
There are no cycles without progress: every transition strictly moves the system closer to a final *Finished* state. Hence, the protocol is **deadlock‑free** under the stated assumptions.

**Potential Deadlock under Message Loss**
If messages can be lost, a deadlock scenario can arise:
1. Coordinator sends PREPARE to all participants.
2. Some participants receive PREPARE, vote COMMIT, and send their votes back, but the coordinator never receives those votes because they are lost.
3. The coordinator, waiting indefinitely for votes, stays in *WaitingForVotes*.
4. Participants that voted are now in *WaitingForDecision* awaiting the final decision, which never arrives because the coordinator never transitions out of *WaitingForVotes*.
Both sides wait forever – a classic deadlock caused by lost messages.

**Mitigation – Timeout‑Based Presumed Abort**
- **Coordinator Timeout**: After sending PREPARE, start a timer `T_coord`. If `T_coord` expires before all votes are received, the coordinator assumes an abort and sends ABORT to all participants.
- **Participant Timeout**: After sending its vote, each participant starts a timer `T_part`. If `T_part` expires without receiving a decision, it assumes the transaction was aborted and rolls back locally.
- **Thresholds**: The timeout values should be chosen based on expected network latency plus a safety margin (e.g., `T_coord = 5 s`, `T_part = 5 s`).
- **Abort Action**: On timeout, the participant discards any tentative changes and optionally logs a warning; the coordinator discards the transaction and notifies participants of the abort.

With these timeouts, even if messages are lost, the system makes progress toward a safe abort, eliminating the deadlock.
