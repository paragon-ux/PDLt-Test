would this response have a valid solution? I did 01-01 on --reasoning high, to test the edge case of reasoning before we change the protocol, and it failed due to exceeding the 10m step budget: import itertools, json, sys
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

Partly. The program is correct and would print a valid partition if it ran to completion, but its search is too inefficient to finish inside 10M steps. So the budget did what it should: this is a method failure, not a routing failure.

Why it would be correct

It lists every candidate triple where a + b = c with three distinct values, using the list's values only.
The backtracking tries sets of 15 non-overlapping triples in index order. Any valid partition, taken in that order, is one of the sets it visits, so it finds a solution if one exists.
The duplicate triples, (a,b,c) and (b,a,c), don't break it. They share every element, so both can never be chosen together.
A cheap sanity check passes. The list sums to 3410, which is even, as it must be because the total is twice the sum of the c values. That rules out nothing, though, and I can't tell from here whether a solution exists. That's the grader's ground truth.
Why it blew the budget

Duplicates double the search. Every triple appears twice.
No forced choice. At every level it may pick any remaining triple. The search is roughly all ordered subsets of about 15 disjoint triples, before a dead end is noticed.
The standard pruning is missing. The largest unused number can never be a summand, so it must be the c of its own triple. Branching only on "largest unused x, and a pair (a, x−a) with both unused" is usually enough. That cuts the branching drastically, and a search built that way usually finishes well within the STANDARD tier.
What this says about the protocol

Jev's STANDARD prediction was reasonable for a competent algorithm. The model chose a naive one, and the 125 exit shows the budget containing it deterministically.
High reasoning effort still produced the naive search. So reasoning level isn't the lever for 01-01; the choice of search method is.
The harness can't supply that choice. Pointing the model at "branch on the largest element" would be coaching the method, which GUARD-03/04 and the anti-overfitting gate forbid. That keeps 01-01 a model-capability boundary, not something the protocol should fix.
One thing I can't check from here is whether this WITNESS line matches the harness's parser: the WITNESS:  prefix and the evidence.path / data layout. On this run it never got that far, so it didn't matter.
Is it as simple as making a optimal prompt standard? do you think that would make a difference?

Not quite. A generic efficiency clause could help a little, but it probably won't change 01-01 by itself.

What such a standard could legitimately say. Something like "choose a method whose cost fits the declared execution budget, and prefer searches that cut off dead branches early." That stays task-neutral, because it names a constraint of the environment, not a method. It doesn't break the guardrails the way "branch on the largest element" would. The model gets told a limit, not the answer.

Why I'd expect a small effect:

The model already knows the goal. Nobody writes a naive search because they were never told to be efficient. It happens because the model doesn't recognize the problem as exact cover with a forced choice. A clause saying "be efficient" doesn't supply that insight. Your high-reasoning run is evidence of this: more thinking still produced the naive search.
It pulls against existing plan rules. PLAN-05 and PLAN-06 keep the plan minimal and forbid researching the task. Requiring a complexity argument in the plan pushes the other way, and the model can simply claim "this is efficient" without it being true.
The budget already enforces it. Exit 125 is the real efficiency standard. Restating it in prose is the kind of prohibition ADR-0016 says doesn't hold.
Levers that probably matter more:

Tell the model its budget at execution time. If EXECUTE doesn't already show the step limit (I can't check that from here), showing it is the environment-aware version of your idea.
Make the repair finding precise. "The program exceeded its 10M-step budget before producing output" is a factual finding with no coaching. That is the one point where the model is most likely to rethink the method. A HEAVY tier with 2 repairs gives it two chances.
Measure before believing. 01-01 is noisy, so one run with a new clause proves nothing. Run it 5–10 times with and without the clause and compare pass rates. If the rate doesn't move, the clause is just noise in the standards.
A prompt standard alone won't close the gap. The budget plus precise repair findings is the protocol's side; recognizing the right algorithm is the model's.

I feel like the standard (just one clause for the planning step) + the budget at execution time would be the hammer and nail of this problem. It is also easy to validate because if the plan pseudocode has any mention of efficiency then you would know it's working

The pairing is sound, but checking whether the plan mentions efficiency wouldn't tell you it's working.

Why the pairing is sound.

The plan clause fits the existing standards. PLAN-02 already says the plan should show enough procedure for the user to reject a materially undesirable approach. An exponential search that can't finish in the budget is exactly that, so a clause like "the plan states the search strategy and why its cost fits the execution budget" makes PLAN-02 more specific instead of fighting it.
The budget at execution time closes the loop. The plan commits to a strategy, and the step limit tests whether it holds.
Why a mention check isn't validation.

It measures compliance, not effect. The model will quickly learn to write "use an efficient search with pruning" and then emit the same naive program. A mention shows it read the clause, not that the method changed. In the 01-01 run above, the program called itself "exact cover backtracking" and still had no pruning.
It's a keyword gate. Scoring plans on the word "efficiency" is the kind of vocabulary check GUARD-02/04 and ADR-0016 moved away from.
What to measure instead, all mechanical and already recorded:

Pass rate on 01-01 over repeated runs, 5–10 with the clause and 5–10 without.
Steps used on the passing and failing attempts: does the median drop?
How often exit 125 appears across the suite, before and after.
Plan-to-program consistency: when the plan names a pruning rule, does the program implement it? This is a manual spot check, but it's the real test.
One thing to confirm before building it. The plan clause only works if the plan stage knows the budget. In the current flow, Jev routes the execution profile at execution time, after the plan is confirmed, so the tier may not exist yet when the plan is drafted. You'd need to either route the budget before drafting the plan or phrase the clause without a number, e.g. "state the strategy's cost". I can't check the engine's order from a side question; worth confirming in the main conversation.

I think that's the problem is that we basically would need to enforce it as a negative prohibition then, what about at the DRAFT_PLAN stage? why can't we just reject then?

You can reject at DRAFT_PLAN, but only on something the host can check. At that stage no program exists yet, so a plan's cost can't be measured. A deterministic rejection would have to key on the plan's wording, which is the keyword gate we removed. There are two ways to reject there without that.

1. Make cost a required field in the schema, not a prohibition. This is Pydantic's territory, but as a positive requirement. Add a required field to the plan's wire payload, for example declared_cost: Literal["WITHIN_100K", "WITHIN_10M", "WITHIN_100M", "BEYOND_100M"], next to the pseudocode. Then:

At DRAFT_PLAN: a missing or invalid value fails the schema. If the declared cost is above the largest budget the environment offers, the plan is rejected with a factual finding: "the plan declares a cost beyond the environment's step budget." That check is deterministic and involves no judgment about meaning.
At EXECUTE: the declaration becomes a claim the sandbox tests. A program that declared WITHIN_10M and hit exit 125 gets the repair finding "the plan declared WITHIN_10M; the program exceeded 10M steps before producing output." That's the sharpest non-coaching feedback available, because it holds the model to its own stated estimate.
It also fixes the ordering problem. The plan stage doesn't need to know the tier in advance, because the model declares one and the host checks it later. You could also choose the budget as the larger of Jev's prediction and the model's declaration.
The model can still lie ("WITHIN_10M" on a naive search), but the lie is caught mechanically at execution. That's the same witness-authority pattern already used for results: a model-asserted claim stays provisional until the sandbox reproduces it.

2. Have Jev judge the plan's cost. Pass the plan text to the execution-profile recipe at DRAFT_PLAN. If Jev predicts BEYOND_100M with probability above 0.5, reject with a finding. This is a discrete routing decision, so it stays within the invariants. The downsides:

It uses Jev as a critic of plan quality, which is close to Axiom 1's "route sandbox conditions, not the model".
It adds a call on every plan.
A false rejection costs a redraft.
I'd use it only as a second check behind option 1.

Why not simply reject on wording: a check for "is this search efficient?" run on plan text is a semantic judgment. A regex does it badly, and a model does it without being authoritative. The user already has that gate, since PLAN-02 exists so the user can reject an undesirable approach. You chose to leave that autonomy with the user when you had me revert the re-plan feature.

Option 1 gives you the enforcement you wanted: a schema-required positive declaration, a deterministic rejection when it exceeds the environment, and a sandbox check of the claim. It's worth building in the main conversation after the full run, and it touches the plan wire schema, the plan standard (both copies plus manifest hashes), and the repair findings.

ok I will probably ask the main chat about the pre-emptive model output. But that might affect the actual output which we don't really want - maybe we can just use a one-way Jev classification

Yes, that's the cleaner option. A required cost field changes what the solver is asked to produce, so it could change the plan and program you're trying to measure. A one-way Jev classification watches the plan without feeding anything back to the solver.

How it would work

Once the plan is confirmed, Jev gets the confirmed prompt, the plan and the environment, and predicts the step tier, using the same recipe and 0.85 quantile as now.
Nothing about the prediction goes into the solver's context, so its inputs stay exactly as they are.
The prediction only drives decisions the host already owns. Pick how far it goes:
Telemetry only. Record the plan-based prediction next to the steps actually used. This shows whether Jev can judge a procedure's cost at all, and it changes nothing.
Budget selection. Use the higher of the request-based and plan-based predictions to pick the tier. A plan describing a heavier search gets a bigger budget, and a naive plan doesn't get a false MINIMAL.
Refusal gate. Reuse the existing budget gate: if P(BEYOND_100M) > 0.5, refuse or cancel before execution with a factual message to the user. This ends the attempt, but it still doesn't coach the model.
Why it stays within the invariants

It routes a sandbox condition. Predicting how many steps a procedure needs is a question about the execution environment, not a grade of the model's quality, so it fits Axiom 1.
It sends no feedback. Without a redraft loop there's no path by which the prediction steers the solver. GUARD-01 (no harness feedback in solver inputs) holds trivially.
Every outcome can be traced to a cause. A failure is either Jev's routing or the model's method, and the events log shows which.
Caveats

Extra calls: one more Jev call per plan, or none if it replaces the current execution-time prediction instead of adding to it.
Noisy on hard plans: Jev may spread its guesses across tiers for difficult plans. The span rule then falls back to STANDARD, so a diffuse prediction wastes nothing.
Unchecked detail: the execution-profile recipe already runs at execution time. I can't tell from a side question whether it already sees the plan or only the request, so check that in the main conversation. If it only sees the request, the change could be as small as passing the plan into its state.
I'd start with option 1 for a run or two. If Jev's plan-based predictions track the steps actually used, move to option 2.

