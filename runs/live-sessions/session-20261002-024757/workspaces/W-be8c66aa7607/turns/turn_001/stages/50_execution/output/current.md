UNVERIFIED ANSWER: Substantive verification was not completed after repair attempts. Reason: [STEP_BUDGET_EXCEEDED] Python block 1 was stopped after 100,000 steps without finishing. Rule: The step budget counts every executed bytecode instruction of the program's own code, including each loop and comprehension iteration; standard-library and built-in internals are not counted. A program's step count is the number of candidates or iterations it visits times the work done for each. Next attempt: The next attempt has the same budget of 100,000 steps. Submit a program whose step count for this input fits within it. If the result cannot be obtained within the budget, run a program that attempts it, emit no witness, and mark the requirement open with the defect recorded.; [WITNESS_NOT_PRINTED] No witness was established: Missing witness in Result IR for task requiring verified execution. Host observation: the deliverable contains no program that ran successfully. Rule: A result that must be certified is certified by a line of the form `WITNESS: <json>` printed by a program the host runs. Next attempt: Include in the deliverable a Python program that prints its result as a `WITNESS: <json>` line; the host runs it. If the result cannot be obtained, emit no witness and mark the requirement open with the defect recorded.

Attempt 1: STEP_BUDGET_EXCEEDED, WITNESS_NOT_PRINTED
Attempt 2: STEP_BUDGET_EXCEEDED, WITNESS_NOT_PRINTED

Candidate deliverable:
import json, random, math

def estimate_probability(samples=50000):
    count = 0
    for _ in range(samples):
        x, y = random.random(), random.random()
        if x > y:
            x, y = y, x
        l1 = x
        l2 = y - x
        l3 = 1.0 - y
        L_min = min(l1, l2, l3)
        L_max = max(l1, l2, l3)
        if L_min / L_max >= 0.25:
            count += 1
    return count / samples

prob = estimate_probability()
print('WITNESS:', json.dumps({
    "polarity": "positive",
    "data": {"probability": prob, "description": "Estimated probability that L_min/L_max >= 1/4"}
}))
