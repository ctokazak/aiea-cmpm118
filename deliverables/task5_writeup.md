---
title: "Task 5: Understanding Logical Reasoning — Logic-LM"
subtitle: "Colby Okazaki · CMPM 118 (AIEA Lab) · Symbolic + Logic + Human-centered"
---

**Repository:** <https://github.com/ctokazak/aiea-cmpm118> (folder `task5_logic_lm/`) · **Slides:** `deliverables/task5_logic_lm_slides.pptx` (9 slides) · **Paper:** Pan et al., *Logic-LM*, Findings of EMNLP 2023 (arXiv:2305.12295)

## The paper in brief

Logic-LM has an LLM **translate** a reasoning problem into a symbolic program (a problem formulator). A deterministic **solver** then does the reasoning: Pyke for PrOntoQA and ProofWriter, Prover9 for FOLIO, python-constraint for LogicalDeduction, and Z3 for AR-LSAT. A **result interpreter** maps the solver's output to an answer, and a **self-refiner** sends solver error messages back to the LLM to fix programs that don't run. With GPT-4 it scores 79.66 on ProofWriter (vs. 68.11 for chain-of-thought) and 87.63 on LogicalDeduction (vs. 75.25). Averaged over all models and datasets, it gains 39.2% over standard prompting and 18.4% over chain-of-thought. The main limitation is translation: the program is only as correct as the LLM's formalization.

## Getting the authors' code running

I cloned `teacherpeterpan/Logic-LLM` and ran its solver stage (`models/logic_inference.py`) on the PrOntoQA logic programs the authors released, then ran their `evaluation.py`. No API key was needed, because the LLM translations are already in the repo. One fix was needed: the Pyke solver imports Python's `imp` module, which was removed in Python 3.12, so I ran it in a Python 3.11 environment.

| Programs written by | Paper | My run |
|---|---|---|
| GPT-4 | 83.20 | **83.20** |
| gpt-3.5-turbo | 61.00 | **59.00** |

GPT-4 matches exactly. For gpt-3.5, 45 of the 500 programs fail to execute and get a **random** backup answer, which explains the 2-point gap.

## My reimplementation

`logic_lm.py` follows the same four stages, using tools I can run for free:

- **Formulator:** `qwen2.5:3b` running locally in Ollama, with a few-shot prompt (`prompts/formulate.txt`). It writes Prolog in which every predicate ends with a truth value, e.g. `shy(alex, false)`, matching the paper's Pyke format `Shy($x, False)`.
- **Solver:** SWI-Prolog in a subprocess with a time limit. Every predicate is **tabled**, so recursive rules always terminate.
- **Interpreter:** the query is proven → True; the query with its truth value flipped is proven → False; neither → Unknown (or False on closed-world data).
- **Self-refiner:** sends syntax errors, or a query predicate that the program never defines, back to the model (up to 2 rounds). If it still fails, the backup is the model's direct answer.

**Test on my Task 4 KB.** `course_kb_problems.py` writes the course KB out as English sentences and builds 14 true/false questions. The gold answers come from querying `courses.pl` directly.

| Run | Direct prompting | Logic-LM | Programs that ran |
|---|---|---|---|
| Course KB, first prompt | 28.6% | 35.7% | 92.9% |
| Course KB, prompt with predicate descriptions | 28.6% | **57.1%** | 100% |
| PrOntoQA, first 30 dev problems | 33.3% | 20.0% | 60.0% |

## What I learned and what went wrong

- With my first prompt, the model **flipped argument order** (it defined `prerequisite(Course, Prereq)` and then queried `prerequisite(cse20, cse130)`) and **invented facts** (e.g., "Jordan passed CSE 12"). The program ran, so self-refinement couldn't catch it. Adding the paper's idea of describing each predicate first (`% prerequisite(C, P, T) ::: Is P a prerequisite of C?`) and saying "never add facts the problem does not state" raised accuracy from 35.7% to 57.1%.
- On PrOntoQA, Logic-LM did **worse** than direct prompting (20% vs 33%; both are below the 50% you'd get by guessing). Only 60% of programs ran, and 17 of 30 answers were *Unknown*. The 3B model often breaks the 5-hop chain: it gets the first fact wrong, skips a link, or turns "not metallic" into `metallic(X, true)`. The solver then correctly answers *Unknown*. That's the paper's main limitation: errors move from reasoning to translation. They're easier to inspect, but a small model makes too many of them. The paper's 83% needed GPT-4 as the translator.
- **Issues:** My laptop has 8 GB of RAM, so I couldn't run a 7B model alongside everything else, and the PrOntoQA run was interrupted twice (the laptop went to sleep), so I made `evaluate.py` save each answer and resume where it stopped. I limited the run to 30 problems because each one takes 15–110 s on my laptop.

## Next steps

- Run the formulator with a larger model (`qwen2.5:7b` or bigger) as a Nautilus GPU Job, to see how much of the PrOntoQA gap comes from model size.
- Evaluate on the full PrOntoQA dev set, not 30 problems, so the accuracy differences are statistically meaningful.
- Add a check that catches invented facts (every fact in the program must match a sentence in the problem), since self-refinement only catches programs that fail to run.
- Join a team and add it to the Notion projects database.
