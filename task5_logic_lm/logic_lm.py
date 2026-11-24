"""A small reimplementation of Logic-LM (Pan et al., EMNLP Findings 2023) with
SWI-Prolog as the symbolic solver and a local LLM served by Ollama.

Pipeline (same four stages as the paper):
  1. Problem formulator  - the LLM translates a natural-language problem into a
                           Prolog program plus a query.
  2. Symbolic reasoner   - SWI-Prolog runs the program (in a subprocess, with a
                           time limit and tabling so recursive rules terminate).
  3. Result interpreter  - the solver's outcome is mapped back to an answer.
  4. Self-refiner        - if the program has a syntax error or the query uses a
                           predicate the program never defines, the error message
                           is sent back to the LLM to fix the program (up to N rounds).

Truth-valued encoding. Like the paper's Pyke programs (``Shy($x, False)``), every
property predicate carries its truth value as the last argument, e.g.
``shy(alex, false)``. That lets the solver tell the three outcomes apart:
  - query provable                 -> True
  - query with flipped value proven -> False
  - neither                         -> Unknown
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:3b"
PROMPTS = Path(__file__).with_name("prompts")


# --------------------------------------------------------------------------- LLM
def llm(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 1024) -> str:
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": max_tokens, "num_ctx": 8192},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())["response"]


# ------------------------------------------------------------------ formulator
def formulate(context: str, question: str, model: str) -> str:
    template = (PROMPTS / "formulate.txt").read_text()
    prompt = template.replace("[[CONTEXT]]", context).replace("[[QUESTION]]", question)
    return extract_program(llm(prompt, model))


def refine(program: str, error: str, model: str) -> str:
    template = (PROMPTS / "self_refine.txt").read_text()
    prompt = template.replace("[[PROGRAM]]", program).replace("[[ERROR]]", error)
    return extract_program(llm(prompt, model))


def extract_program(text: str) -> str:
    """Take the first fenced code block if there is one, otherwise the raw text."""
    m = re.search(r"```(?:prolog|pl)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


# ---------------------------------------------------------------------- solver
@dataclass
class SolverResult:
    answer: str | None          # "True" / "False" / "Unknown", or None on error
    error: str = ""


QUERY_RE = re.compile(r"^\s*\?-\s*(.+?)\.?\s*$", re.M)
HEAD_RE = re.compile(r"^\s*([a-z][A-Za-z0-9_]*)\s*\(", re.M)


def split_program(program: str) -> tuple[str, str | None]:
    """Separate the clauses from the '?- query.' line."""
    m = QUERY_RE.search(program)
    query = m.group(1).strip() if m else None
    clauses = QUERY_RE.sub("", program)
    return clauses, query


def arity(term_args: str) -> int:
    depth, n = 0, 1
    for ch in term_args:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "," and depth == 0:
            n += 1
    return n


def defined_predicates(clauses: str) -> set[str]:
    """name/arity for every clause head (facts and rule heads)."""
    preds = set()
    no_comments = "\n".join(ln.split("%")[0] for ln in clauses.splitlines())
    for line in re.split(r"\.(?=\s|$)", no_comments):
        line = " ".join(line.split())
        if not line or line.startswith("%") or line.startswith(":-"):
            continue
        head = line.split(":-")[0]
        m = re.match(r"([a-z][A-Za-z0-9_]*)\s*\((.*)\)\s*\.?\s*$", head.strip())
        if m:
            preds.add(f"{m.group(1)}/{arity(m.group(2))}")
    return preds


def flip(query: str) -> str | None:
    """shy(alex, false) -> shy(alex, true). None if there is no truth argument."""
    m = re.match(r"^(.*),\s*(true|false)\s*\)\s*$", query)
    if not m:
        return None
    return f"{m.group(1)}, {'false' if m.group(2) == 'true' else 'true'})"


def solve(program: str, closed_world: bool = False, time_limit: int = 5) -> SolverResult:
    clauses, query = split_program(program)
    if not query:
        return SolverResult(None, "The program has no query. Add one line of the form `?- predicate(args).`")

    preds = defined_predicates(clauses)
    qm = re.match(r"([a-z][A-Za-z0-9_]*)\s*\((.*)\)\s*$", query)
    if not qm:
        return SolverResult(None, f"The query `{query}` is not a single predicate call like `name(arg1, arg2)`.")
    qpred = f"{qm.group(1)}/{arity(qm.group(2))}"
    if qpred not in preds:
        return SolverResult(None, (
            f"The query uses {qpred}, but no fact or rule defines {qpred}. "
            f"Defined predicates are: {', '.join(sorted(preds)) or '(none)'}. "
            "Use the same predicate name and number of arguments in the query as in the facts and rules."))

    tables = "\n".join(f":- table {p}." for p in sorted(preds))
    header = (":- style_check(-discontiguous).\n:- style_check(-singleton).\n"
              ":- use_module(library(time)).\n" + tables + "\n")
    opposite = flip(query)
    runner = f"""
prove(G, R) :- catch(call_with_time_limit({time_limit}, (G -> R = yes ; R = no)),
                     E, (E = error(existence_error(_, _), _) -> R = no ; (print_message(error, E), R = err))).
main :- prove(({query}), A), writeln(query=A),
        {"prove((" + opposite + "), B), writeln(opposite=B)" if opposite else "writeln(opposite=none)"}.
"""
    with tempfile.TemporaryDirectory() as tmp:
        prog = Path(tmp, "program.pl")
        prog.write_text(header + clauses + "\n" + runner)
        try:
            proc = subprocess.run(
                ["swipl", "-q", "-f", "none", "-g", "consult('program.pl')", "-g", "main", "-t", "halt"],
                cwd=tmp, capture_output=True, text=True, timeout=time_limit * 3 + 10)
        except subprocess.TimeoutExpired:
            return SolverResult(None, "The solver timed out.")
    out, err = proc.stdout, proc.stderr
    errors = [ln for ln in err.splitlines() if "error" in ln.lower() or "syntax" in ln.lower()]
    if errors or "query=" not in out:
        msg = "\n".join(errors[:6]) or err.strip()[:600] or "The program could not be loaded."
        return SolverResult(None, re.sub(r"\S*program\.pl", "program.pl", msg))

    q = re.search(r"query=(\w+)", out).group(1)
    o = re.search(r"opposite=(\w+)", out).group(1)
    if q == "yes" and o == "yes":
        return SolverResult(None, f"The program proves both `{query}` and `{opposite}`; the facts or rules contradict each other.")
    if q == "yes":
        return SolverResult("True")
    if o == "yes":
        return SolverResult("False")
    return SolverResult("False" if closed_world else "Unknown")


# -------------------------------------------------------------------- pipeline
@dataclass
class Trace:
    programs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    answer: str | None = None
    status: str = ""            # "solved", "solved after refinement", "backup"


def logic_lm(context: str, question: str, model: str = DEFAULT_MODEL,
             max_refinements: int = 2, closed_world: bool = False) -> Trace:
    t = Trace()
    program = formulate(context, question, model)
    for round_ in range(max_refinements + 1):
        t.programs.append(program)
        res = solve(program, closed_world=closed_world)
        if res.answer is not None:
            t.answer = res.answer
            t.status = "solved" if round_ == 0 else f"solved after {round_} refinement(s)"
            return t
        t.errors.append(res.error)
        if round_ < max_refinements:
            program = refine(program, res.error, model)
    # Backup, like the paper's "LLM" backup strategy: fall back to the plain LLM answer.
    t.answer = direct(context, question, model)
    t.status = "backup (direct LLM)"
    return t


def direct(context: str, question: str, model: str = DEFAULT_MODEL) -> str:
    """Standard-prompting baseline: ask the LLM for the answer directly."""
    prompt = (f"{context}\n\nQuestion: {question}\n"
              "Answer with exactly one word: True, False, or Unknown.\nAnswer:")
    text = llm(prompt, model, max_tokens=8).strip().lower()
    for word in ("true", "false", "unknown"):
        if word in text:
            return word.capitalize()
    return "Unknown"
