"""Build the Task 5 (Logic-LM) and Task 6 (Datalog) slide decks as .pptx.

Usage: ../.venv/bin/python make_slides.py
Reads the Task 5 result files so the numbers on the slides match the runs.
"""
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).parent
ROOT = HERE.parent
INK = RGBColor(0x1F, 0x23, 0x30)
MUTED = RGBColor(0x5B, 0x63, 0x73)
ACCENT = RGBColor(0x00, 0x5A, 0x9C)     # UCSC-ish blue
GOLD = RGBColor(0xF2, 0xA9, 0x00)
LIGHT = RGBColor(0xEE, 0xF3, 0xF8)
CODE_BG = RGBColor(0xF4, 0xF4, 0xF4)
AUTHOR = "Colby Okazaki · AIEA Lab auditor (CMPM 118), Fall 2026"


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(13.333), Inches(7.5)
        self.blank = self.prs.slide_layouts[6]
        self.n = 0

    def _text(self, slide, x, y, w, h, text, size=20, color=INK, bold=False,
              font="Calibri", align=PP_ALIGN.LEFT):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.word_wrap = True
        lines = text if isinstance(text, list) else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = line
            run.font.size, run.font.color.rgb, run.font.bold = Pt(size), color, bold
            run.font.name = font
            p.alignment = align
        return box

    def _frame(self, title, kicker=None):
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.18), self.prs.slide_height)
        bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()
        if kicker:
            self._text(s, 0.7, 0.35, 11, 0.4, kicker.upper(), 13, ACCENT, True)
        self._text(s, 0.7, 0.65, 12, 0.9, title, 32, INK, True)
        self._text(s, 0.7, 7.0, 9, 0.35, AUTHOR, 11, MUTED)
        self._text(s, 12.0, 7.0, 0.8, 0.35, str(self.n), 11, MUTED, align=PP_ALIGN.RIGHT)
        return s

    def title(self, title, subtitle, note):
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        bg.fill.solid(); bg.fill.fore_color.rgb = ACCENT; bg.line.fill.background()
        self._text(s, 0.9, 2.2, 11.5, 1.8, title, 40, RGBColor(255, 255, 255), True)
        self._text(s, 0.9, 4.1, 11.5, 0.8, subtitle, 20, RGBColor(0xDD, 0xE8, 0xF3))
        self._text(s, 0.9, 6.3, 11.5, 0.5, note, 14, RGBColor(0xDD, 0xE8, 0xF3))

    def bullets(self, title, items, kicker=None, size=22):
        s = self._frame(title, kicker)
        box = s.shapes.add_textbox(Inches(0.7), Inches(1.75), Inches(11.9), Inches(5.1))
        tf = box.text_frame; tf.word_wrap = True
        for i, item in enumerate(items):
            sub = item.startswith("  ")
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = ("– " if sub else "• ") + item.strip()
            run.font.size = Pt(size - 4 if sub else size)
            run.font.color.rgb = MUTED if sub else INK
            run.font.name = "Calibri"
            p.level = 1 if sub else 0
            p.space_after = Pt(8)
        return s

    def code(self, s, x, y, w, h, text, size=14):
        bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        bg.fill.solid(); bg.fill.fore_color.rgb = CODE_BG; bg.line.fill.background()
        self._text(s, x + 0.15, y + 0.1, w - 0.3, h - 0.2, text.splitlines(), size, INK, font="Menlo")

    def table(self, s, x, y, w, rows, col_w=None, size=14, highlight_col=None):
        nr, nc = len(rows), len(rows[0])
        shape = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(0.42 * nr))
        t = shape.table
        if col_w:
            for i, cw in enumerate(col_w):
                t.columns[i].width = Inches(cw)
        for r in range(nr):
            for c in range(nc):
                cell = t.cell(r, c)
                cell.text = str(rows[r][c])
                para = cell.text_frame.paragraphs[0]
                para.font.size = Pt(size)
                para.font.bold = r == 0 or (highlight_col is not None and c == highlight_col)
                para.font.color.rgb = RGBColor(255, 255, 255) if r == 0 else INK
                cell.fill.solid()
                cell.fill.fore_color.rgb = ACCENT if r == 0 else (LIGHT if r % 2 else RGBColor(255, 255, 255))
        return shape

    def flow(self, s, y, steps, w=2.6, gap=0.45, x0=0.7):
        for i, (head, body) in enumerate(steps):
            x = x0 + i * (w + gap)
            box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(1.9))
            box.fill.solid(); box.fill.fore_color.rgb = LIGHT; box.line.color.rgb = ACCENT
            self._text(s, x + 0.12, y + 0.12, w - 0.24, 0.5, head, 17, ACCENT, True)
            self._text(s, x + 0.12, y + 0.62, w - 0.24, 1.25, body, 13, INK)
            if i < len(steps) - 1:
                arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + w + 0.05), Inches(y + 0.75),
                                         Inches(gap - 0.1), Inches(0.4))
                arr.fill.solid(); arr.fill.fore_color.rgb = GOLD; arr.line.fill.background()

    def save(self, path):
        self.prs.save(path)
        print("wrote", path, f"({self.n} slides)")


def pct(x):
    return f"{100 * x:.1f}%"


# ---------------------------------------------------------------- Task 5 deck
def task5():
    res = ROOT / "task5_logic_lm" / "results"
    kb = json.loads((res / "course_kb_qwen2.5-3b_v2_predicate_descriptions.json").read_text())["summary"]
    pq_file = res / "prontoqa_qwen2.5-3b.json"
    pq = json.loads(pq_file.read_text())["summary"] if pq_file.exists() else None
    kb7_file = res / "course_kb_qwen2.5-7b.json"
    kb7 = json.loads(kb7_file.read_text())["summary"] if kb7_file.exists() else None

    d = Deck()
    d.title("Logic-LM: Empowering LLMs with Symbolic Solvers for Faithful Logical Reasoning",
            "Liangming Pan, Alon Albalak, Xinyi Wang, William Yang Wang · Findings of EMNLP 2023 · arXiv:2305.12295",
            "Task 5 paper summary and reimplementation · Colby Okazaki · AIEA Lab, Fall 2026")

    d.bullets("LLMs can sound logical without being logical", [
        "Chain-of-thought answers can be right for the wrong reasons, or wrong with confident steps",
        "Nothing guarantees each step follows from the premises: the reasoning is not faithful",
        "Symbolic solvers (Prolog, theorem provers, SAT/SMT) are exact and explainable…",
        "  …but they need the problem already written in formal logic",
        "Idea: let the LLM do what it is good at (translating language) and the solver do the reasoning",
    ], kicker="Motivation")

    s = d._frame("The Logic-LM pipeline", "Method")
    d.flow(s, 1.9, [
        ("1. Problem formulator", "The LLM reads the problem and writes a symbolic version: predicates, facts, rules, query (few-shot prompt)."),
        ("2. Symbolic reasoner", "A deterministic solver runs the program. Every step it takes is valid by construction."),
        ("3. Result interpreter", "Maps the solver's output back to an answer (True / False / Unknown, or A–E)."),
        ("4. Self-refiner", "If the program fails to parse or run, the solver's error message goes back to the LLM to fix it."),
    ])
    d._text(s, 0.7, 4.3, 12, 2.4, [
        "If the program still fails after refinement, Logic-LM falls back to a backup answer (random, or the CoT answer).",
        "Key claim: the answer is faithful to the formulation. Errors move from 'reasoning' to 'translation', where they are visible.",
    ], 18, MUTED)

    s = d._frame("One solver per kind of problem", "Method")
    d.table(s, 0.7, 1.8, 11.9, [
        ["Dataset", "Kind of reasoning", "Formulation", "Solver"],
        ["PrOntoQA", "Deductive, fictional ontology (5 hops)", "Logic program", "Pyke"],
        ["ProofWriter", "Deductive, open world (depth 5)", "Logic program", "Pyke"],
        ["FOLIO", "First-order logic, real-world text", "FOL formulas", "Prover9"],
        ["LogicalDeduction", "Ordering puzzles", "Constraint satisfaction", "python-constraint"],
        ["AR-LSAT", "LSAT analytical reasoning", "SAT / SMT", "Z3"],
    ], col_w=[2.4, 4.3, 2.8, 2.4], size=16)
    d.code(s, 0.7, 4.95, 11.9, 1.75,
           "Facts:  Tumpuses(Alex, True)\n"
           "Rules:  Tumpuses($x, True) >>> Vumpuses($x, True)\n"
           "        Dumpus($x, True) >>> Shy($x, False)\n"
           "Query:  Shy(Alex, False)          ← PrOntoQA program in the paper's Pyke format", 15)

    s = d._frame("Results: Logic-LM beats standard prompting on every dataset", "Results (paper, Table 2)")
    d.table(s, 0.7, 1.75, 11.9, [
        ["Dataset", "GPT-4 Standard", "GPT-4 CoT", "GPT-4 Logic-LM", "ChatGPT Logic-LM"],
        ["PrOntoQA", "77.40", "98.79", "83.20", "61.00"],
        ["ProofWriter", "52.67", "68.11", "79.66", "58.33"],
        ["FOLIO", "69.11", "70.58", "78.92", "62.74"],
        ["LogicalDeduction", "71.33", "75.25", "87.63", "65.67"],
        ["AR-LSAT", "33.33", "35.06", "43.04", "26.41"],
    ], col_w=[2.9, 2.2, 2.2, 2.4, 2.2], size=16, highlight_col=3)
    d._text(s, 0.7, 4.55, 12, 2.3, [
        "Average gain: +39.2% over standard prompting, +18.4% over chain-of-thought.",
        "Gains grow with reasoning depth (ProofWriter depth 0→5).",
        "Exception: on PrOntoQA, GPT-4 CoT (98.79) beats Logic-LM (83.20). Errors are in translation, not reasoning.",
        "Self-refinement mostly raises the executable rate (FOLIO +17.6 pts for GPT-3.5); accuracy gains are small.",
    ], 17, INK)

    d.bullets("Limitations the authors point out", [
        "Translation is the bottleneck: “transforming problems into logical forms remains a challenging task”",
        "  GPT-4 still forgets to define predicates, swaps “above” and “below”, writes invalid FOL",
        "The answer is only as good as the formulation, and a wrong program gives a confident wrong answer",
        "Bounded by the solver's expressiveness: not every problem fits first-order logic",
        "Self-refinement fixes syntax errors, not semantic ones (a program that runs but means the wrong thing)",
    ], kicker="Discussion")

    s = d._frame("Running the authors' code", "My reproduction")
    d._text(s, 0.7, 1.75, 6.0, 4.8, [
        "I ran the paper's solver (models/logic_inference.py, Pyke) on the logic programs the authors released for PrOntoQA, then their evaluation script.",
        "",
        "Pyke imports the removed `imp` module, so it needs Python ≤ 3.11.",
        "",
        "No API key was needed: the LLM step was already done by the authors.",
    ], 17, INK)
    d.table(s, 7.0, 1.8, 5.6, [
        ["Programs from", "Paper", "My run"],
        ["GPT-4", "83.20", "83.20"],
        ["gpt-3.5-turbo", "61.00", "59.00"],
    ], col_w=[2.2, 1.7, 1.7], size=17)
    d._text(s, 7.0, 3.3, 5.6, 2.5, [
        "GPT-4 matches exactly. The gpt-3.5 gap is the random backup answer for the 45 programs that fail to execute.",
    ], 15, MUTED)

    s = d._frame("My reimplementation: Prolog + a local 3B model", "My reproduction")
    d.flow(s, 1.75, [
        ("Formulate", "qwen2.5:3b (Ollama, local, free) writes Prolog with a truth-value argument: shy(alex, false)."),
        ("Solve", "SWI-Prolog in a subprocess, with tabling so recursive rules always terminate."),
        ("Interpret", "Query proven → True. Flipped query proven → False. Neither → Unknown."),
        ("Self-refine", "Syntax errors or an undefined query predicate go back to the model (up to 2 rounds)."),
    ])
    d.code(s, 0.7, 3.95, 11.9, 1.4,
           "% predicates\n% prerequisite(C, P, T) ::: Is P a prerequisite of C?\n"
           "prerequisite(C, P, true) :- requires(C, P, true).\n?- prerequisite(cse130, cse20, true).", 14)
    d._text(s, 0.7, 5.5, 12, 1.3, [
        "Test sets: 14 questions generated from my Task 4 course KB (gold answers from Prolog), and the first 30 PrOntoQA dev problems.",
    ], 16, MUTED)

    rows = [["Test set", "Model", "Direct", "Logic-LM", "Programs ran"],
            ["Course KB (14)", "qwen2.5:3b", pct(kb["direct_accuracy"]), pct(kb["logic_lm_accuracy"]),
             pct(kb["executable_rate_with_refinement"])]]
    if kb7:
        rows.append(["Course KB (14)", "qwen2.5:7b", pct(kb7["direct_accuracy"]), pct(kb7["logic_lm_accuracy"]),
                     pct(kb7["executable_rate_with_refinement"])])
    if pq:
        rows.append([f"PrOntoQA (first {pq['n']})", "qwen2.5:3b", pct(pq["direct_accuracy"]), pct(pq["logic_lm_accuracy"]),
                     pct(pq["executable_rate_with_refinement"])])
    s = d._frame("What I found", "My reproduction")
    d.table(s, 0.7, 1.75, 11.9, rows, col_w=[2.8, 2.3, 2.1, 2.4, 2.3], size=17, highlight_col=3)
    d._text(s, 0.7, 2.0 + 0.45 * len(rows), 12, 3.2, [
        "On my course KB, the solver doubled accuracy. On PrOntoQA, it lowered it: a 3B model can't translate 5-hop problems reliably.",
        "My first prompt scored 35.7% on the course KB: the model flipped argument order and invented facts. "
        "Adding the paper's predicate descriptions (“Shy($x, bool) ::: Is x shy?”) raised it to 57.1%.",
        "On PrOntoQA the 3B model often breaks the 5-hop chain (wrong first fact, missing links), so the solver says Unknown (17 of 30). "
        "These are translation errors, exactly the paper's main limitation. It needs a stronger model (the paper used GPT-4).",
    ], 17, INK)
    return d


# ---------------------------------------------------------------- Task 6 deck
def task6():
    d = Deck()
    d.title("Datalog: logic programming for databases",
            "Task 6: researching other logics + LLMs",
            "Colby Okazaki · AIEA Lab, Fall 2026 · primer: Datalog primer (UMONS); my code: task6_other_logics/")

    d.bullets("What is Datalog?", [
        "A subset of Prolog: facts and if-then rules over relations, with no function symbols",
        "  parent(ann, bob).   ancestor(X, Y) :- parent(X, Y).",
        "Every program has exactly one answer (its least model), and it is always finite",
        "Evaluated bottom-up: start from the facts and apply rules until nothing new appears",
        "Used in databases (recursive SQL), program analysis (Soufflé, CodeQL), security policies, and knowledge graphs",
    ], kicker="Overview")

    s = d._frame("Datalog vs. Prolog", "Comparison")
    d.table(s, 0.7, 1.75, 11.9, [
        ["", "Prolog", "Datalog"],
        ["Terms", "Any terms, lists, f(x)", "Constants and variables only"],
        ["Evaluation", "Top-down search (SLD resolution)", "Bottom-up, to a fixed point"],
        ["Termination", "Can loop forever (left recursion)", "Always terminates"],
        ["Rule order", "Matters", "Doesn't matter: it's purely declarative"],
        ["Negation", "\\+ (negation as failure)", "Stratified negation: compute p fully before using 'not p'"],
        ["Safety", "No restriction", "Every head variable must appear in a positive body atom"],
    ], col_w=[2.2, 4.6, 5.1], size=16)

    s = d._frame("How evaluation works: semi-naive fixed point", "Semantics")
    d.code(s, 0.7, 1.75, 5.6, 2.2,
           "edge(a,b). edge(b,c).\nedge(c,a). edge(c,d).\n\npath(X,Y) :- edge(X,Y).\npath(X,Y) :- path(X,Z), edge(Z,Y).", 15)
    d.table(s, 6.7, 1.75, 5.9, [
        ["Round", "New path facts"],
        ["1", "a→b, b→c, c→a, c→d"],
        ["2", "a→c, b→a, b→d, c→b"],
        ["3", "a→a, a→d, b→b, c→c"],
        ["4", "(none: fixed point)"],
    ], col_w=[1.2, 4.7], size=15)
    d._text(s, 0.7, 4.3, 12, 2.4, [
        "Semi-naive: each round only joins with facts that were new last round, so no work is repeated.",
        "Plain Prolog loops forever on this left-recursive rule. SWI-Prolog needs “:- table path/2.” to match Datalog.",
        "My engine (datalog.py, ~250 lines, standard library) and tabled SWI-Prolog give the same answers.",
    ], 17, INK)

    s = d._frame("Negation has to be stratified", "Semantics")
    d.code(s, 0.7, 1.75, 11.9, 1.25,
           "blocked(S, C)  :- missing(S, C, _).\n"
           "can_take(S, C) :- student(S), course(C), not passed(S, C), not blocked(S, C).", 15)
    d._text(s, 0.7, 3.2, 12, 3.4, [
        "'not blocked' is only safe to check after blocked is fully computed, so blocked goes in a lower stratum.",
        "A program like  p(X) :- n(X), not q(X).   q(X) :- n(X), not p(X).  has no stratification, so it is rejected.",
        "This is how my Task 4 course KB ports to Datalog: same 8 queries, same answers as Prolog.",
    ], 18, INK)

    d.bullets("Why Datalog matters for LLMs + logic", [
        "A safe target language for LLM translation: no infinite loops, no side effects, and rule order doesn't matter",
        "Easy to check: run the program and every derived fact has a proof tree you can show the user",
        "Close to SQL, which LLMs already write well, so text-to-Datalog builds on text-to-SQL",
        "Used in neuro-symbolic work, e.g. Scallop (differentiable Datalog) and LLM-generated rules for knowledge graphs",
        "Limits: no arithmetic or function symbols in pure Datalog; recursion through negation is not allowed",
    ], kicker="LLMs + logic")

    d.bullets("Takeaways", [
        "Datalog = Prolog without function symbols, plus guaranteed termination",
        "Bottom-up fixed-point evaluation; semi-naive makes it efficient",
        "Safety + stratified negation keep every program finite with a single meaning",
        "Code: task6_other_logics/datalog.py, examples/*.dl, test_datalog.py (5 tests pass)",
        "One-page tutorial: task6_other_logics/TUTORIAL.md",
    ], kicker="Summary")
    return d


if __name__ == "__main__":
    task5().save(HERE / "task5_logic_lm_slides.pptx")
    task6().save(HERE / "task6_datalog_slides.pptx")
