"""A small Datalog engine: parser + bottom-up semi-naive evaluation with
stratified negation. Standard library only.

Syntax (a subset of standard Datalog):
    edge(a, b).                          % fact
    path(X, Y) :- edge(X, Y).            % rule
    path(X, Z) :- path(X, Y), edge(Y, Z).
    unreachable(X, Y) :- node(X), node(Y), not path(X, Y).   % negation
    ?- path(a, X).                       % query

Constants start lowercase (or are numbers / 'quoted'); variables start uppercase or _.

Usage:
    python datalog.py program.dl         # prints every query's answers
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass


# ----------------------------------------------------------------- data types
@dataclass(frozen=True)
class Atom:
    pred: str
    args: tuple[str, ...]
    negated: bool = False

    def __str__(self):
        s = f"{self.pred}({', '.join(self.args)})"
        return f"not {s}" if self.negated else s


@dataclass(frozen=True)
class Rule:
    head: Atom
    body: tuple[Atom, ...]


def is_var(term: str) -> bool:
    return term[0].isupper() or term[0] == "_"


# --------------------------------------------------------------------- parser
TOKEN = re.compile(r"\s*(?:(%[^\n]*)|(\?-|:-|[(),.])|('[^']*'|[A-Za-z_][A-Za-z0-9_]*|-?\d+))")


def tokenize(text):
    pos, out = 0, []
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise SyntaxError(f"unexpected character at {text[pos:pos + 20]!r}")
        pos = m.end()
        if m.group(1):                      # comment
            continue
        tok = m.group(2) or m.group(3)
        if tok:
            out.append(tok)
    return out


def parse(text):
    """Return (facts, rules, queries)."""
    toks, i = tokenize(text), 0
    facts, rules, queries = set(), [], []

    def atom():
        nonlocal i
        neg = False
        if toks[i] == "not":
            neg, i = True, i + 1
        pred = toks[i]; i += 1
        args = []
        if i < len(toks) and toks[i] == "(":
            i += 1
            while toks[i] != ")":
                args.append(toks[i]); i += 1
                if toks[i] == ",":
                    i += 1
            i += 1
        return Atom(pred, tuple(args), neg)

    while i < len(toks):
        if toks[i] == "?-":
            i += 1
            queries.append(atom())
        else:
            head = atom()
            if toks[i] == ":-":
                i += 1
                body = [atom()]
                while toks[i] == ",":
                    i += 1
                    body.append(atom())
                rules.append(Rule(head, tuple(body)))
                check_safe(rules[-1])
            else:
                if any(is_var(a) for a in head.args):
                    raise ValueError(f"fact {head} contains a variable")
                facts.add((head.pred, head.args))
        if toks[i] != ".":
            raise SyntaxError(f"expected '.' but found {toks[i]!r}")
        i += 1
    return facts, rules, queries


def check_safe(rule: Rule):
    """Range restriction: every variable in the head or in a negated atom must
    appear in some positive body atom. This is what keeps Datalog finite."""
    positive = {a for b in rule.body if not b.negated for a in b.args if is_var(a)}
    risky = [a for a in rule.head.args if is_var(a)]
    risky += [a for b in rule.body if b.negated for a in b.args if is_var(a)]
    unsafe = sorted({v for v in risky if v not in positive and v != "_"})
    if unsafe:
        raise ValueError(f"unsafe rule {rule.head} :- ...: variables {unsafe} are not bound by a positive atom")


# ---------------------------------------------------------- stratification
def stratify(rules):
    """Group rules into strata so a predicate is fully computed before any rule
    negates it. Raises if negation goes through a cycle (not stratifiable)."""
    idb = {r.head.pred for r in rules}
    stratum = {p: 0 for p in idb}
    changed = True
    while changed:
        changed = False
        for r in rules:
            for b in r.body:
                if b.pred not in idb:
                    continue
                need = stratum[b.pred] + (1 if b.negated else 0)
                if stratum[r.head.pred] < need:
                    stratum[r.head.pred] = need
                    changed = True
                    if need > len(idb):
                        raise ValueError("program is not stratifiable (negation in a cycle)")
    layers = defaultdict(list)
    for r in rules:
        layers[stratum[r.head.pred]].append(r)
    return [layers[k] for k in sorted(layers)]


# ------------------------------------------------------------- evaluation
def match(atom, fact_args, env):
    env = dict(env)
    for term, val in zip(atom.args, fact_args):
        if is_var(term):
            if term == "_":
                continue
            if env.setdefault(term, val) != val:
                return None
        elif term != val:
            return None
    return env


def body_solutions(body, db, delta=None, delta_pos=None):
    """Join the body atoms left to right. If delta_pos is given, that atom reads
    only from `delta` (the facts new in the last round): this is semi-naive."""
    envs = [{}]
    for k, atom in enumerate(body):
        if atom.negated:
            envs = [e for e in envs
                    if (atom.pred, tuple(e.get(t, t) for t in atom.args)) not in db.all]
            continue
        source = delta if k == delta_pos else db
        new_envs = []
        for e in envs:
            for args in source.by_pred.get(atom.pred, ()):
                if len(args) == len(atom.args):
                    m = match(atom, args, e)
                    if m is not None:
                        new_envs.append(m)
        envs = new_envs
    return envs


class DB:
    def __init__(self, facts=()):
        self.all = set()
        self.by_pred = defaultdict(set)
        for f in facts:
            self.add(f)

    def add(self, fact):
        if fact in self.all:
            return False
        self.all.add(fact)
        self.by_pred[fact[0]].add(fact[1])
        return True


def evaluate(facts, rules, stats=None):
    db = DB(facts)
    rounds = 0
    for layer in stratify(rules):
        # first round: fire every rule against everything known
        delta = DB()
        for r in layer:
            for env in body_solutions(r.body, db):
                fact = (r.head.pred, tuple(env.get(t, t) for t in r.head.args))
                if fact not in db.all:
                    delta.add(fact)
        layer_preds = {r.head.pred for r in layer}
        while delta.all:
            rounds += 1
            for f in delta.all:
                db.add(f)
            new = DB()
            for r in layer:
                # semi-naive: at least one recursive body atom must use a new fact
                for k, b in enumerate(r.body):
                    if b.negated or b.pred not in layer_preds:
                        continue
                    for env in body_solutions(r.body, db, delta, k):
                        fact = (r.head.pred, tuple(env.get(t, t) for t in r.head.args))
                        if fact not in db.all:
                            new.add(fact)
            delta = new
    if stats is not None:
        stats["rounds"] = rounds
        stats["facts"] = len(db.all)
    return db


def answer(db, query):
    rows = []
    for args in sorted(db.by_pred.get(query.pred, ())):
        env = match(query, args, {})
        if env is not None:
            rows.append(env)
    return rows


def run(text):
    facts, rules, queries = parse(text)
    stats = {}
    db = evaluate(facts, rules, stats)
    results = []
    for q in queries:
        rows = answer(db, q)
        variables = [a for a in q.args if is_var(a) and a != "_"]
        if not variables:
            results.append((q, "true" if rows else "false"))
        else:
            seen = sorted({tuple(r[v] for v in variables) for r in rows})
            results.append((q, [dict(zip(variables, s)) for s in seen]))
    return results, stats


def main():
    text = open(sys.argv[1]).read()
    results, stats = run(text)
    for q, res in results:
        if isinstance(res, str):
            print(f"?- {q}.  {res}")
        else:
            body = "; ".join(", ".join(f"{k}={v}" for k, v in r.items()) for r in res)
            print(f"?- {q}.  {len(res)} answer(s): {body or '(none)'}")
    print(f"% {stats['facts']} facts after {stats['rounds']} semi-naive round(s)")


if __name__ == "__main__":
    main()
