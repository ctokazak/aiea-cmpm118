> **TODO before submitting:** write the Reflection section below in your own words, then delete this box.

**Repository:** <https://github.com/ctokazak/aiea-cmpm118> (file `task3_symbolic_basics/3_symbolic_crash_course_completed.ipynb`)

## What I did

I worked through the symbolic logic crash-course notebook in Python 3 (it ran under 3.9.6) using only the standard library. For every **Predict** question I wrote my answer before running the cell, completed all four exercises, and ran the notebook top to bottom. **Every check cell prints `Checks passed`.**

| Section | What I implemented | Result |
|---|---|---|
| 1. Propositions and implication | `implies(p, q)` as `(not p) or q`, and `equivalent(p, q)` as implication both ways | Matches the truth table in all 4 rows |
| 2. Translation and counterexamples | Searched all assignments of R ("registered") and A ("has access") for counterexamples | Affirming the consequent has one counterexample, `(R=False, A=True)`; modus ponens has none |
| 3. Forward chaining | `infer(facts, rules)`, which applies rules until nothing new is added and returns a new set | Same closure with the rules in either order; input set unchanged |
| 4. Explanations | `explain_access(known)`, returning `derived`, `missing` and a `trace` of fired rules | With both records: derived, trace `eligible_lee → access_lee`. Without the training record: not derived, missing `completed_training_lee` |

## Key ideas

- **Implication isn't causation, and it doesn't reverse.** P → Q is false in only one row (P true, Q false). So P = False, Q = True makes P → Q true and Q → P false.
- **Valid vs. invalid inference** can be checked mechanically: an argument is valid exactly when no assignment makes every premise true and the conclusion false.
- **Forward chaining needs a fixed point.** One pass over the rules isn't enough when a rule depends on a fact that a later rule produces, so `infer` loops until no new facts are added.
- **"Not derived" is not "false."** With the training record missing, the system can't show Lee is eligible. That doesn't prove Lee is ineligible, but the policy still denies access.

## Exercise 4: missing records and contestability

The written response in the notebook puts the policy in plain language: access requires eligibility, and eligibility requires both registration and completed training. It describes Lee, who registered and finished training, but whose attendance sheet was never uploaded. Neither rule fires, and Lee is shown "no access", even though the system never decided Lee *didn't* complete training. It only failed to find a record (the closed-world assumption). So the result should read "access not granted: missing completed_training_lee", not "Lee is ineligible." To contest it, Lee is shown `derived = False` and the `missing` set, submits evidence such as a training certificate, and a person reviews it and adds the fact. The rules are then re-run, and the trace shows which rule changed the outcome.

## Next steps

- Carry the "not derived ≠ false" idea into Prolog: Task 4's `can_take` rule uses `\+`, which makes the same closed-world assumption.
- Reuse `explain_access`'s idea (report the `missing` facts, not just yes/no) when explaining Prolog answers in Tasks 4 and 5.

## Reflection

[Write 3–5 sentences in your own words: what you learned, what surprised you, and how it connects to Tasks 4–6.]
