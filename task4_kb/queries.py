"""Run the same queries against courses.pl two ways and check they agree:

1. the swipl command-line interpreter (a subprocess), and
2. SWI-Prolog embedded in Python through janus_swi.

Usage: python queries.py            (from this folder, inside the project venv)
"""
from pathlib import Path
import subprocess

import janus_swi as janus

KB = Path(__file__).with_name("courses.pl")

# (description, goal, variables to collect)
QUERIES = [
    ("Direct prerequisites of CSE 101", "prereq(cse101, P)", ["P"]),
    ("All prerequisites of CSE 140 (recursive)", "requires(cse140, P)", ["P"]),
    ("Courses Colby can take next", "can_take(colby, C)", ["C"]),
    ("Courses Maya can take next", "can_take(maya, C)", ["C"]),
    ("What Jordan is missing for CSE 101", "missing(jordan, cse101, P)", ["P"]),
    ("Students who can take CSE 101", "can_take(S, cse101)", ["S"]),
    ("Prerequisite depth of each course", "course(C, _), depth(C, D)", ["C", "D"]),
    ("Is CSE 20 required for CSE 130?", "requires(cse130, cse20)", []),
    ("Is CSE 140 required for CSE 101?", "requires(cse101, cse140)", []),
]


def canon(rows):
    """Sort and dedupe answers so both engines can be compared directly."""
    return sorted(set(tuple(str(v) for v in row) for row in rows))


def run_swipl(goal, vars_):
    """Ask the swipl binary for all solutions, one per line, fields tab-separated."""
    template = "[" + ",".join(vars_) + "]" if vars_ else "[]"
    prog = (
        f"forall(({goal}), (atomic_list_concat({template}, '\\t', L), writeln(L))), halt."
    )
    out = subprocess.run(
        ["swipl", "-q", "-g", prog, "-t", "halt(1)", str(KB)],
        capture_output=True, text=True, check=True,
    ).stdout
    lines = [ln for ln in out.splitlines()]
    return canon(ln.split("\t") if vars_ else () for ln in lines)


def run_janus(goal, vars_):
    rows = []
    for sol in janus.query(goal):
        if sol["truth"] is True:
            rows.append(tuple(sol[v] for v in vars_))
    return canon(rows)


def show(rows, vars_):
    if not vars_:
        return "true" if rows else "false"
    return ", ".join("/".join(r) for r in rows) or "(no answers)"


def main():
    janus.consult(str(KB))
    all_match = True
    for desc, goal, vars_ in QUERIES:
        a, b = run_swipl(goal, vars_), run_janus(goal, vars_)
        ok = a == b
        all_match &= ok
        print(f"?- {goal}.")
        print(f"   {desc}")
        print(f"   swipl : {show(a, vars_)}")
        print(f"   janus : {show(b, vars_)}")
        print(f"   {'MATCH' if ok else 'MISMATCH'}\n")
    print("All queries match." if all_match else "Some queries differ!")
    raise SystemExit(0 if all_match else 1)


if __name__ == "__main__":
    main()
