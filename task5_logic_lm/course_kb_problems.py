"""Build a natural-language test set from the Task 4 knowledge base (courses.pl).

The context paragraph is generated from the KB's facts, plus the KB's rules written
in English. Gold answers come from querying courses.pl directly with SWI-Prolog
(through janus), so they are exactly what the Task 4 KB says.

Usage: python course_kb_problems.py  -> writes data/course_kb.json
"""
import json
from pathlib import Path

import janus_swi as janus

HERE = Path(__file__).parent
KB = HERE.parent / "task4_kb" / "courses.pl"
janus.consult(str(KB))
# One extra rule stated in the context below.
janus.consult("advanced", "advanced(C) :- prereq(C, cse101).")


def name(code):
    return code.upper().replace("CSE", "CSE ")


def holds(goal):
    return janus.query_once(goal)["truth"] is True


def build_context():
    lines = []
    for s in janus.query("prereq(C, P)"):
        lines.append(f"{name(s['C'])} requires {name(s['P'])}.")
    for s in janus.query("passed(S, C)"):
        lines.append(f"{s['S'].capitalize()} passed {name(s['C'])}.")
    lines += [
        "If a course requires another course, the second course is a prerequisite of the first.",
        "If a course requires a second course and the second course has a prerequisite, that prerequisite is also a prerequisite of the first course.",
        "A student can take CSE 101 if they passed CSE 30, CSE 13S and CSE 16.",
        "Any course that requires CSE 101 is an advanced course.",
    ]
    return " ".join(lines)


QUESTIONS = [
    # (statement, Prolog goal that decides it)
    ("CSE 20 is a prerequisite of CSE 130.", "requires(cse130, cse20)"),
    ("CSE 140 is a prerequisite of CSE 101.", "requires(cse101, cse140)"),
    ("CSE 12 is a prerequisite of CSE 140.", "requires(cse140, cse12)"),
    ("CSE 16 is a prerequisite of CSE 30.", "requires(cse30, cse16)"),
    ("CSE 13S is a prerequisite of CSE 130.", "requires(cse130, cse13s)"),
    ("CSE 30 is a prerequisite of CSE 12.", "requires(cse12, cse30)"),
    ("Colby can take CSE 101.", "can_take(colby, cse101)"),
    ("Maya can take CSE 101.", "can_take(maya, cse101)"),
    ("Jordan can take CSE 101.", "can_take(jordan, cse101)"),
    ("CSE 140 is an advanced course.", "advanced(cse140)"),
    ("CSE 30 is an advanced course.", "advanced(cse30)"),
    ("Maya passed CSE 16.", "passed(maya, cse16)"),
    ("Jordan passed CSE 12.", "passed(jordan, cse12)"),
    ("CSE 20 is a prerequisite of CSE 101.", "requires(cse101, cse20)"),
]


def main():
    context = build_context()
    problems = [{
        "id": f"course_kb_{i}",
        "context": context,
        "question": f"Is the following statement true or false? {stmt}",
        "answer": "True" if holds(goal) else "False",
        "gold_goal": goal,
    } for i, (stmt, goal) in enumerate(QUESTIONS, 1)]
    out = HERE / "data" / "course_kb.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(problems, indent=2))
    print(context, "\n")
    for p in problems:
        print(p["answer"].ljust(6), p["question"].split("? ")[1])


if __name__ == "__main__":
    main()
