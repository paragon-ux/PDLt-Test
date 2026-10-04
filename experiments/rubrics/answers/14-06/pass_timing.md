Invariant: at least one of A, B is RED.

Base: B starts RED.

Step, for each transition: entering RED preserves it; GREEN -> YELLOW does not change which direction is RED; the only risky transition is RED -> GREEN. For B this is guarded: B goes GREEN only when A enters RED. For A there is no guard in the statement, so safety comes from timing: when A enters RED, B goes GREEN immediately, spends 45 s GREEN and 5 s YELLOW and is RED again at 50 s, while A stays RED for 60 s. So when A turns GREEN, B is RED.

Assumptions: B's transition to GREEN happens at the same instant A enters RED; the timers are exact (no drift); transitions are atomic. If any of these fail (e.g. B starts late by more than 10 s), the invariant can break, so a real controller should add an explicit guard on A.
