RESULT IR: put the Result IR in the output's "result_ir" field, not in the deliverable text. The host reads two of its fields:
- "witness": present only when the deliverable claims a result (see WITNESS below).
- "open_defects": present only when a requested result was not obtained; a list of objects, each with a "description" of what was not obtained and why.
Leave "files" and "reconciliation" as empty lists.

WITNESS: this task requires verified execution. A claimed result is certified by a Python program in the deliverable that prints exactly one line to standard output: the text "WITNESS: " followed by a JSON object. Build the object as a Python dict in the program and print it with json.dumps; do not write the JSON by hand inside a string. The object's fields:
- A result was found: "polarity" is "positive" and "data" is an object holding the result under descriptive keys.
- The result is shown not to exist by a search the program ran: "polarity" is "negative", "basis" is "search", "search_exhausted" is true, "nodes_explored" is the number of states the program explored, and "method" names the search.
- The result is shown not to exist by an argument rather than a computation: "polarity" is "negative", "basis" is "proof", and "argument" states the argument.
If the result was not obtained, print no witness and describe what was not obtained in "open_defects".
The host runs the program; the witness it prints replaces any witness written into "result_ir". A witness the host did not reproduce is reported as provisional.
