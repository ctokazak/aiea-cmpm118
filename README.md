# CMPM 118 (AIEA Lab): onboarding Tasks 2–6

Colby Okazaki · Fall 2026 · topic: **Symbolic + Logic + Human-centered** (NeuroSymbolic AI: LLMs and Logic)

| Task | Folder | What's there |
|---|---|---|
| 2. Nautilus | [`task2_nautilus/`](task2_nautilus/) | PVC, deployment and job YAML for training a CIFAR-10 CNN on a GPU, plus `run_task2.sh`, which runs each step in order |
| 3. Symbolic logic basics | [`task3_symbolic_basics/`](task3_symbolic_basics/) | Completed notebook with outputs (all checks pass) |
| 4. Build your own KB | [`task4_kb/`](task4_kb/) | `courses.pl` (26 facts, 5 rules) and `queries.py`, which runs 9 queries in `swipl` and through janus and checks they match |
| 5. Logic-LM | [`task5_logic_lm/`](task5_logic_lm/) | Reimplementation of Logic-LM with SWI-Prolog and a local LLM (Ollama), evaluated on the Task 4 KB and PrOntoQA, plus a run of the authors' own solver |
| 6. Other logics: Datalog | [`task6_other_logics/`](task6_other_logics/) | `datalog.py` (a semi-naive Datalog engine with stratified negation), examples, tests, and a one-page tutorial |
| Write-ups and slides | [`deliverables/`](deliverables/) | One-page write-ups and the Task 5 and Task 6 slide decks |

## Setup (macOS)

```bash
brew install swi-prolog python@3.12 ollama pandoc
python3.12 -m venv .venv
.venv/bin/pip install janus-swi python-pptx nbclient ipykernel
ollama serve &            # in another terminal
ollama pull qwen2.5:3b    # and qwen2.5:7b for the larger run
```

## Reproduce

```bash
# Task 4
cd task4_kb && ../.venv/bin/python queries.py

# Task 5
cd task5_logic_lm
../.venv/bin/python course_kb_problems.py            # builds data/course_kb.json from the Task 4 KB
../.venv/bin/python evaluate.py course_kb            # Logic-LM vs direct prompting
../.venv/bin/python evaluate.py prontoqa --limit 50

# Task 6
cd task6_other_logics && ../.venv/bin/python test_datalog.py && ../.venv/bin/python datalog.py examples/graph.dl

# Slides
cd deliverables && ../.venv/bin/python make_slides.py
```

The authors' Logic-LM code (<https://github.com/teacherpeterpan/Logic-LLM>) needs Python ≤ 3.11, because the Pyke solver imports the removed `imp` module. Its PrOntoQA results are saved in `task5_logic_lm/reference_run/`.
