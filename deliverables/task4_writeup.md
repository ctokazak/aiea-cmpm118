---
title: "Task 4: Build Your Own KB"
subtitle: "Colby Okazaki · CMPM 118 (AIEA Lab) · Symbolic + Logic + Human-centered"
---

**Repository:** <https://github.com/ctokazak/aiea-cmpm118> (folder `task4_kb/`)

## Getting the tools running

I installed SWI-Prolog 11.0.0 with Homebrew (`brew install swi-prolog`) on an Apple M3 MacBook running macOS 27. For the Python side I used **janus**, the official SWI-Prolog bridge (`pip install janus-swi`, version 1.5.3), inside a Python 3.12 virtual environment. Two setup issues came up:

- The macOS system Python is 3.9, and janus needs a newer Python, so I installed `python@3.12` with Homebrew and made a project venv (`python3.12 -m venv .venv`).
- `pip install janus-swi` builds against the installed SWI-Prolog, so SWI-Prolog has to be installed first. After that, `import janus_swi` worked with no extra configuration.

## The knowledge base

`courses.pl` models a set of UCSC-style CS courses, their prerequisites, and three students' transcripts. It has **26 facts** (8 `course/2`, 8 `prereq/2`, 10 `passed/2`) and **5 rules**:

| Rule | Meaning |
|---|---|
| `requires(C, P)` | P is a direct **or indirect** prerequisite of C (recursive) |
| `missing(S, C, P)` | student S hasn't passed prerequisite P of course C |
| `can_take(S, C)` | S passed every prerequisite of C and hasn't taken C yet (uses negation as failure) |
| `student(S)` | S has passed at least one course |
| `depth(C, D)` | length of the longest prerequisite chain under C (recursive, with `aggregate_all`) |

## Tests

`queries.py` runs nine queries twice: once with the `swipl` command-line interpreter (as a subprocess) and once inside Python through janus. It then checks that both give identical, sorted answers. **All 9 matched.**

| Query | Answer |
|---|---|
| `prereq(cse101, P)` | cse13s, cse16, cse30 |
| `requires(cse140, P)` | cse101, cse12, cse13s, cse16, cse20, cse30 |
| `can_take(colby, C)` | cse101 |
| `can_take(maya, C)` | cse13s, cse30 |
| `missing(jordan, cse101, P)` | cse13s, cse16 |
| `can_take(S, cse101)` | colby |
| `course(C,_), depth(C, D)` | cse20/0, cse16/0, cse30/1, cse12/1, cse13s/2, cse101/3, cse130/4, cse140/4 |
| `requires(cse130, cse20)` | true |
| `requires(cse101, cse140)` | false |

I checked these answers by hand against the prerequisite chain (20 → 12 → 13S → 101 → 130/140). The full output is in `task4_kb/results.txt`.

## What I learned

The recursive `requires` rule only works with the base case listed first and the recursive call last. If it is left-recursive, Prolog's depth-first search would loop. `can_take` taught me that `\+` is negation *as failure*: Maya "can't take CSE 101" only because the KB has no record of her passing CSE 30, not because it says she failed it. The same KB is reused in Task 5 to test Logic-LM and in Task 6, where I rewrote it in Datalog and got the same answers.

## Next steps

- Add an `explain(S, C, Why)` rule that returns the full chain of missing prerequisites, like Task 3's `explain_access`, so a "no" comes with a reason.
- Extend it with course offerings per quarter and unit limits, so `can_take` needs more than one kind of constraint.
