"""Tests for datalog.py.  Run: python test_datalog.py"""
import subprocess
from pathlib import Path

from datalog import parse, run

HERE = Path(__file__).parent
EX = HERE / "examples"


def answers(results, i):
    return results[i][1]


def test_courses_match_task4():
    """The Datalog KB gives the same answers as the Prolog KB from Task 4."""
    res, _ = run((EX / "courses.dl").read_text())
    assert [r["P"] for r in answers(res, 0)] == ["cse13s", "cse16", "cse30"]
    assert len(answers(res, 1)) == 6
    assert [r["C"] for r in answers(res, 2)] == ["cse101"]
    assert [r["C"] for r in answers(res, 3)] == ["cse13s", "cse30"]
    assert [r["P"] for r in answers(res, 4)] == ["cse13s", "cse16"]
    assert [r["S"] for r in answers(res, 5)] == ["colby"]
    assert answers(res, 6) == "true" and answers(res, 7) == "false"


def test_cycle_terminates_and_matches_tabled_prolog():
    """Bottom-up evaluation handles the left-recursive rule on a cyclic graph, and
    agrees with SWI-Prolog when Prolog uses tabling (:- table path/2)."""
    res, _ = run((EX / "graph.dl").read_text())
    ours = sorted(r["Y"] for r in answers(res, 0))
    prog = ":- table path/2.\n" + "\n".join(
        ln for ln in (EX / "graph.dl").read_text().splitlines()
        if ln.startswith(("edge", "node", "path(X, Y) :-")))
    out = subprocess.run(
        ["swipl", "-q", "-g", "consult(user)", "-g",
         "forall(path(a,Y), writeln(Y)), halt"],
        input=prog, capture_output=True, text=True, timeout=30).stdout
    assert ours == sorted(set(out.split())) == ["a", "b", "c", "d"]


def test_plain_prolog_loops_on_left_recursion():
    """Without tabling, Prolog's top-down search never finishes on this rule."""
    prog = "edge(a,b). edge(b,a).\npath(X,Y) :- path(X,Z), edge(Z,Y).\npath(X,Y) :- edge(X,Y).\n"
    out = subprocess.run(
        ["swipl", "-q", "-g", "consult(user)", "-g",
         "catch(call_with_time_limit(2, forall(path(a,Y), true)), E, (print(E), nl)), halt"],
        input=prog, capture_output=True, text=True, timeout=30)
    text = out.stdout + out.stderr
    assert "time_limit_exceeded" in text or "stack" in text.lower()


def test_unsafe_rule_rejected():
    try:
        parse("p(X, Y) :- q(X).")
    except ValueError as e:
        assert "unsafe" in str(e)
    else:
        raise AssertionError("unsafe rule was accepted")


def test_unstratifiable_rejected():
    try:
        run("n(a). p(X) :- n(X), not q(X). q(X) :- n(X), not p(X).")
    except ValueError as e:
        assert "stratifiable" in str(e)
    else:
        raise AssertionError("negation cycle was accepted")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("passed:", name)
