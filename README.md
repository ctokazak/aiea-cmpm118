# CMPM 118 (AIEA Lab): onboarding Tasks 2–6

Colby Okazaki · Fall 2026 · topic: **Symbolic + Logic + Human-centered** (NeuroSymbolic AI: LLMs and Logic)

| Task | Folder | What's there |
|---|---|---|
| 2. Nautilus | [`task2_nautilus/`](task2_nautilus/) | PVC, deployment and job YAML for training a CIFAR-10 CNN on a GPU, plus `run_task2.sh`, which runs each step in order |
| 3. Symbolic logic basics | [`task3_symbolic_basics/`](task3_symbolic_basics/) | Completed notebook with outputs (all checks pass) |
| 4. Build your own KB | [`task4_kb/`](task4_kb/) | `courses.pl` (26 facts, 5 rules) and `queries.py`, which runs 9 queries in `swipl` and through janus and checks they match |
| 5. Logic-LM | [`task5_logic_lm/`](task5_logic_lm/) | Reimplementation of Logic-LM with SWI-Prolog and a local LLM (Ollama), evaluated on the Task 4 KB and PrOntoQA, plus a run of the authors' own solver |
| 6. Other logics: Datalog | [`task6_other_logics/`](task6_other_logics/) | `datalog.py` (a semi-naive Datalog engine with stratified negation), examples, tests, and a one-page tutorial |
| Write-ups and slides | [`deliverables/`](deliverables/) | Write-ups, research diary, Datalog tutorial and the Task 5 and Task 6 slide decks, as PDFs |

## Status (Nov 24, 2026)

| Task | Status | Submit |
|---|---|---|
| 2 | Done: JupyterHub, PVC, Deployment and Job all run; Deployment and Job deleted, PVC `ctokazak-task2` kept | `deliverables/task2_writeup.pdf` (page 2 is the log screenshot) |
| 3 | Done except final reflection wording | `task3_symbolic_basics/3_symbolic_crash_course_completed.ipynb` (Restart & Run All first) |
| 4 | Done | `deliverables/task4_writeup.pdf` |
| 5 | Done; still need to join a team and add it to the Notion projects database | `deliverables/task5_writeup.pdf`, `task5_logic_lm_slides.pdf` |
| 6 | Done | `deliverables/task6_writeup.pdf`, `task6_datalog_tutorial.pdf`, `task6_datalog_slides.pdf` |

Other to-dos: present the write-ups at the auditor status meetings, upload to Canvas, keep `deliverables/research_diary.md` up to date, and delete the PVC (`kubectl delete -f task2_nautilus/pvc.yaml`) once Task 2 is graded.

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
../.venv/bin/python evaluate.py prontoqa --limit 30

# Task 6
cd task6_other_logics && ../.venv/bin/python test_datalog.py && ../.venv/bin/python datalog.py examples/graph.dl

# Slides and PDFs
cd deliverables && ../.venv/bin/python make_slides.py && ./make_pdfs.sh
```

### On another computer

```bash
git clone https://github.com/ctokazak/aiea-cmpm118.git && cd aiea-cmpm118
```

Then follow the setup above. On Windows, install SWI-Prolog, Python 3.12, Ollama and pandoc from their websites (or with `winget`), make the venv with `py -3.12 -m venv .venv`, and use `.venv\Scripts\python` in place of `.venv/bin/python`. For Task 2, install `kubectl` and `kubelogin` and download the cluster config from <https://nrp.ai/config> to `~/.kube/config`. `make_pdfs.sh` and the Keynote export only run on macOS.

The authors' Logic-LM code (<https://github.com/teacherpeterpan/Logic-LLM>) needs Python ≤ 3.11, because the Pyke solver imports the removed `imp` module. Its PrOntoQA results are saved in `task5_logic_lm/reference_run/`.
