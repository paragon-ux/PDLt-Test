Invariant: not both directions non-RED.

Base: B starts RED. Inductive step: transitions into RED preserve the invariant. GREEN -> YELLOW preserves it because the other direction is RED. RED -> GREEN preserves it because B only turns GREEN when A enters RED, so the other direction is RED. Therefore all transitions preserve the invariant and by induction it always holds. No further assumptions are needed.
