---
title: "Research Diary"
---

Times are Pacific. Results and logs referred to here are in <https://github.com/ctokazak/aiea-cmpm118>.

## Thu 2026-10-22

- Added my profile to the lab website (`aiea-lab.github.io`, commit "Adding Colby Okazaki user profile").

## Mon 2026-11-23

**16:03–16:06 · Tool setup for Tasks 4–5**

- Installed SWI-Prolog and Python 3.12 with Homebrew and made the project venv (`python3.12 -m venv .venv`). The macOS system Python is 3.9, too old for `janus-swi`, which is why I needed 3.12.
- Installed Ollama and pulled `qwen2.5:3b` to use as the local LLM for Logic-LM.
- *Worked:* `janus-swi` built cleanly once SWI-Prolog was installed first.

**16:44 · Nautilus access (Task 2)**

- Downloaded the cluster config from nrp.ai and installed `kubelogin`. The config doesn't work without it, which the instructions don't mention.
- *Didn't work:* `kubectl get pods -n aiea-auditors` returned **Forbidden**. Login worked, but I wasn't in the namespace yet. Asked in the Nautilus Discord.

**~18:00 · Datalog engine (Task 6)**

- Ran `datalog.py`, my semi-naive Datalog engine with stratified negation, on the examples. Installed pandoc to turn write-ups into Word files.

**Next:** get added to the namespace, run the CIFAR-10 deployment and job, and finish the ProntoQA evaluation.

## Tue 2026-11-24

**Before 13:00 · Nautilus runs (Task 2)**

- Added to `aiea-auditors`. Created the 5Gi PVC, then ran `cifar10train.py` in a deployment on an **NVIDIA TITAN Xp** (`Device: cuda:0`): 55% test accuracy. Then ran the same script as a Job: 4m23s, 52%.
- *Didn't work well:* the first CIFAR-10 download took about 30 minutes at ~95 KB/s. *Fix:* the data was on the PVC, so the Job didn't download it again.
- Deleted the deployment and job afterward so they didn't hold a GPU. Kept the PVC.

**13:00 · First commit** of Tasks 2–6 to GitHub.

**13:17 · ProntoQA results (Task 5)**

- Finished the 30-problem run with `qwen2.5:3b`: Logic-LM 20.0% vs. direct prompting 33.3%. Only 60% of the generated programs ran.
- *Why it didn't work:* the 3B model breaks the 5-hop chains (wrong first fact, a skipped link, negation as `metallic(X, true)`), so the solver correctly answers *Unknown*. Errors moved from reasoning into translation.

**13:19–14:00 · Write-ups and slides**

- Added the Job log screenshot to the Task 2 write-up.
- Checked both slide decks for text that doesn't fit its box. The Task 5 flow-step headings were too wide at 17pt, so I shrank them to 15pt.
- Wrote the Task 3 write-up and added a "Next steps" section to every write-up.

**13:40–14:02 · JupyterHub (Task 2, item 4)**

- Ran `cifar10_tutorial.ipynb` on a JupyterHub server with a **Tesla V100-SXM2-32GB**. `torch.cuda.is_available()` returned `True`. Took 21m44s (about 19 minutes of it downloading CIFAR-10 again), 53% test accuracy.
- *Noticed:* the tutorial checks for the GPU only in its last cell and never moves the model to it, so training ran on the CPU. My `cifar10train.py` does move it.
- Made the repo public so graders can follow the links in the write-ups.

**Next:** join a Task 5 team and add it to the Notion projects database; run Logic-LM with a larger model as a Nautilus GPU Job; delete the PVC after Task 2 is graded.

## To date (no timestamps on record)

Add the day and time for each of these:

- [date] Task 3: worked through the symbolic logic notebook; all checks pass.
- [date] Task 4: wrote `courses.pl` (26 facts, 5 rules) and `queries.py`; all 9 queries match between `swipl` and janus.
- [date] Task 5: read the Logic-LM paper and reproduced the authors' solver on their saved outputs (GPT-4 83.2%, paper 83.20; gpt-3.5 59.0%, paper 61.0).
- [date] Task 5: built `logic_lm.py` and the course-KB test. Adding predicate descriptions to the prompt raised accuracy from 35.7% to 57.1%.
- [date] Task 5: a 50-problem ProntoQA run was killed partway when my laptop went to sleep (`prontoqa50_qwen2.5-3b_killed_run.log`). *Fix:* `evaluate.py` now saves each answer and resumes.
- [date] Task 6: wrote the Datalog tutorial and the 5 tests.
