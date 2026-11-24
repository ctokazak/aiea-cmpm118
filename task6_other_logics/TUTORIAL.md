# Datalog in one page

**Datalog** is logic programming without function symbols: a program is a set of facts and if-then rules over relations, and its meaning is the set of every fact those rules can derive. Unlike Prolog, a Datalog program always terminates and has exactly one answer.

## 1. Facts, rules, queries

```prolog
parent(ann, bob).  parent(bob, cara).              % facts: lowercase constants
ancestor(X, Y) :- parent(X, Y).                    % rule: "if ... then ancestor"
ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z).    % recursion is allowed
?- ancestor(ann, W).                               % query: W = bob ; W = cara
```

Variables start with an uppercase letter. A comma in a rule body means *and*. Writing several rules with the same head means *or*.

## 2. Two rules that keep every program finite

1. **Safety (range restriction).** Every variable in the head, or in a negated atom, must appear in a positive body atom. `p(X, Y) :- q(X).` is rejected because `Y` could be anything.
2. **Stratified negation.** You may write `not p(...)` only if `p` can be computed completely first. `p(X) :- n(X), not q(X).  q(X) :- n(X), not p(X).` is rejected because each depends negatively on the other.

## 3. How it runs (bottom-up)

Start with the facts. Apply every rule to everything known so far, add the new facts, and repeat until a round adds nothing. That final set is the **least fixed point**. *Semi-naive* evaluation only joins against facts that were new in the previous round, so no derivation is repeated. Because there are no function symbols, only finitely many facts can exist, so evaluation always stops, even for left-recursive rules on cyclic graphs, where plain Prolog loops forever.

## 4. Try it

```bash
cd task6_other_logics
python datalog.py examples/graph.dl      # reachability on a cyclic graph
python datalog.py examples/courses.dl    # the Task 4 course KB, in Datalog
python test_datalog.py                   # 5 tests, including a cross-check against SWI-Prolog
```

```prolog
% examples/graph.dl (excerpt)
edge(a, b). edge(b, c). edge(c, a). edge(c, d).
path(X, Y) :- edge(X, Y).
path(X, Y) :- path(X, Z), edge(Z, Y).               % left recursion: fine in Datalog
unreachable(X, Y) :- node(X), node(Y), not path(X, Y).
?- path(a, Y).          % Y = a, b, c, d   (fixed point after 3 rounds of new facts)
```

In SWI-Prolog you get the same behavior by adding `:- table path/2.` (tabling), which evaluates the predicate the Datalog way.

## 5. Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| A head variable not in the body | Rejected as unsafe | Bind it with a positive atom, e.g. `node(Y)` |
| `not` used before its relation is complete | Not stratifiable | Split it into a separate predicate in a lower stratum |
| Expecting `not p` to mean "p is false" | It means "p was not derived" (closed world) | State missing facts explicitly, or model `unknown` |
| Using `f(X)` or lists | Not Datalog | Flatten into relations, e.g. `item(List, Pos, Value)` |

## 6. Why it's useful with LLMs

Datalog makes a safer target than full Prolog or FOL for an LLM to translate text into. Every program terminates, the order the model writes rules in doesn't matter, and each answer has a proof (the chain of rule firings) that can be shown to a user. It is also close to SQL, which LLMs already write well. Its limits are that pure Datalog has no arithmetic or function symbols, and closed-world negation treats "not derived" as false.

*References:* Datalog primer (UMONS), <https://informatique.umons.ac.be/ssi/teaching/bdIImons/primerDatalog.pdf>; Ceri, Gottlob & Tanca, "What you always wanted to know about Datalog (and never dared to ask)", IEEE TKDE 1989.
