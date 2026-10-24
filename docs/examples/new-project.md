# New project: a fictional museum label command

This is a newly written illustrative walkthrough, not an execution record or
anonymized personal case. Moonseed Museum and its catalog are fictional.

The user asks for a simple local command that turns a JSON specimen catalog
into labels. The overall route has not been chosen. Dumbcane first clarifies
the useful outcome and constraints, then considers existing complete tools
and reusable smaller parts. It presents the evidence, tradeoffs and recommended
route. Product implementation waits for the needed user choice.

If public-source reading is unavailable, the agent says which research was
not performed and keeps the decision open. It does not infer that alternatives
do not exist. If the user already supplied an applicable route decision, the
agent reuses it and proceeds within the authorized scope.

Try the independent task with `python3 -B evals/stage.py new-project NEW_DIR`.
The [evaluation guide](../../evals/README.md) explains what is and is not checked.
