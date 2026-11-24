**Repository:** <https://github.com/ctokazak/aiea-cmpm118> (folder `task6_other_logics/`) · **Tutorial:** `task6_other_logics/TUTORIAL.md` · **Slides:** `deliverables/task6_datalog_slides.pdf` (7 slides)

## Choosing a logic

Of the logics listed (Datalog, LTL, deontic, probabilistic soft logic, fuzzy logic), I chose **Datalog** because it is the closest to the Prolog I used in Tasks 4 and 5, so I could run both on the same knowledge base and compare them directly.

## Getting the tools running

Rather than install a separate Datalog system, I wrote a small engine, `datalog.py` (~250 lines, Python standard library only), to understand how evaluation works. It has:

- a parser for facts, rules, `not`, `?-` queries and `%` comments
- a **safety check**: every head variable and every variable in a negated atom must appear in a positive body atom
- **stratification**: rules are grouped so a relation is fully computed before any rule negates it, and negation cycles are rejected
- **semi-naive evaluation**: each round joins only against facts that were new in the previous round, until a fixed point

To check it, I used SWI-Prolog 11.0.0 with **tabling** (`:- table path/2.`), which gives Prolog the same bottom-up behavior.

## Tests I ran

`test_datalog.py` has 5 tests, and **all pass**:

1. **Same answers as Task 4.** `examples/courses.dl` is my Task 4 course KB rewritten in Datalog (`\+` becomes `not`, and a `blocked/2` helper keeps negation stratified). All 8 queries give exactly the Prolog answers. For example, `can_take(maya, C)` gives cse13s and cse30, and `requires(cse140, P)` gives 6 courses.
2. **Cycles terminate and match tabled Prolog.** `examples/graph.dl` has a cycle a→b→c→a and a left-recursive `path` rule. My engine reaches a fixed point after 3 rounds of new facts, and SWI-Prolog with tabling returns the same set {a, b, c, d}.
3. **Plain Prolog loops.** The same left-recursive rule without tabling hits a time limit in SWI-Prolog. This is the main practical difference between the two.
4. **Unsafe rules are rejected:** `p(X, Y) :- q(X).`
5. **Unstratifiable programs are rejected:** `p :- not q.  q :- not p.` (with a domain atom).

## What I learned

- **Bottom-up vs. top-down.** Prolog searches backward from the query, so rule order and left recursion matter. Datalog builds everything forward from the facts, so neither matters. SWI-Prolog's tabling is the bridge between the two.
- **Negation needs care in both.** Datalog's `not` is still closed-world ("not derived"), the same caveat as Prolog's `\+` from Task 3. Stratification only guarantees a single consistent answer.
- **Connection to LLMs.** In Task 5, my local model's Prolog programs sometimes had argument-order and invented-fact errors, but none of them hung, only because I added tabling. Datalog builds that guarantee into the language, and it is close to SQL, which LLMs already write well. Systems like Scallop (differentiable Datalog) use this for neuro-symbolic learning.

## Next steps

- Have the Task 5 formulator write Datalog instead of Prolog and compare how many programs run and how accurate they are.
- Try one of the other logics listed in the task (e.g., probabilistic soft logic) on the same course KB, to see what it can say that Datalog can't.

**Issue / feedback:** The Datalog primer link was the most useful reading. A short starter `.dl` example in the task folder would help auditors who haven't used Prolog before.
