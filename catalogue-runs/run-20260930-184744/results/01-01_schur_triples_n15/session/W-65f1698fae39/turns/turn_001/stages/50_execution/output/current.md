UNVERIFIED ANSWER: Substantive verification was not completed after repair attempts. Reason: python block 1 exceeded the 10,000,000-step budget in the sandbox (stderr: PDLT_STEP_BUDGET_EXCEEDED: more than 10000000 steps)

Candidate deliverable:
import itertools, json, sys
L = [71,97,54,56,44,158,45,58,82,135,113,117,86,40,12,185,63,50,111,72,90,109,61,13,92,60,91,35,114,94,105,26,15,51,102,118,76,32,108,23,22,134,83,43,64]
L_set = set(L)
# generate all possible triples a,b,c where a+b=c and all distinct
triples = []
for a,b,c in itertools.permutations(L,3):
    if a+b==c and a!=b and a!=c and b!=c:
        triples.append((a,b,c))
# use exact cover backtracking
solution = []
used = set()

def backtrack(start):
    if len(solution)==15:
        return True
    for i in range(start, len(triples)):
        a,b,c = triples[i]
        if a in used or b in used or c in used:
            continue
        # choose
        solution.append((a,b,c))
        used.update([a,b,c])
        if backtrack(i+1):
            return True
        # undo
        solution.pop()
        used.difference_update([a,b,c])
    return False

found = backtrack(0)
if not found:
    print('No solution', file=sys.stderr)
    sys.exit(1)
# output result and witness
print('Solution triples:')
for t in solution:
    print(t)
# produce witness line
witness = {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"triples": solution}}
print('WITNESS: ' + json.dumps(witness))
