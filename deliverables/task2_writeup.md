---
title: "Task 2: Nautilus"
subtitle: "Colby Okazaki · CMPM 118 (AIEA Lab)"
---

> **TODO before submitting:** finish the JupyterHub step (item 4), add the screenshot, then delete this box.

**Repository:** <https://github.com/ctokazak/aiea-cmpm118> (folder `task2_nautilus/`)

## What Nautilus is

Nautilus, run by the National Research Platform (NRP), is a shared Kubernetes cluster of GPU machines spread across many universities. You don't log in to a specific machine. Instead you describe what you want in a YAML file (a container image, CPUs, memory, GPUs, storage) and Kubernetes schedules it on whatever node has room. Our lab's resources live in the `aiea-auditors` **namespace**.

## Getting access

1. Logged in at nrp.ai with my UCSC account through CILogon.
2. Downloaded the cluster config with `curl -o ~/.kube/config https://nrp.ai/config` and installed `kubectl` and `kubelogin` with Homebrew. The config file won't work without kubelogin, which handles the CILogon sign-in.
3. `kubectl get pods -n aiea-auditors` first returned **Forbidden**, because my login worked but I hadn't been added to the namespace yet. I asked in the Nautilus Discord channel and was added on November 24, 2026.
4. JupyterHub: ran the `cifar10_tutorial.ipynb` notebook at jupyterhub-west.nrp-nautilus.io after `pip install`-ing torchvision and matplotlib. [TODO: one sentence on what happened / how long the wait was]

## Deployment, PVC and Job

All three YAML files are in `task2_nautilus/`:

| Resource | Name | Notes |
|---|---|---|
| PVC | `ctokazak-task2` | 5Gi, `rook-cephfs`, mounted at `/data` |
| Deployment | `ctokazak-task2-deploy` | `pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime`, 1 GPU, 2 CPU, 8Gi; `sleep infinity` so I can `kubectl exec` in |
| Job | `ctokazak-task2-job` | same image and PVC; `command` runs `python cifar10train.py`; `restartPolicy: Never` |

**Deployment:** copied `cifar10train.py` into the PVC with `kubectl cp`, ran it with `kubectl exec`, then **deleted the deployment** so it wouldn't hold a GPU while idle. The pod got an **NVIDIA TITAN Xp** (12 GB). The script printed `Device: cuda:0`. Two epochs reached **55%** test accuracy, with the loss falling from 2.199 to 1.301. The run took 2006 s in total, but almost all of that was the first download of CIFAR-10 (170 MB at about 95 KB/s, 30 minutes). Training itself took about 3 minutes. The dataset was saved to the PVC, so the job didn't download it again. Log: `task2_nautilus/logs/deployment_train.log`.

**Job:** applied `job.yaml` on the same PVC (after the deployment's pod was gone, since a PVC can be single-attach) and read the output with `kubectl logs job/ctokazak-task2-job`. Then I deleted the job. The log shows `Device: cuda:0`, so the training ran on the GPU. The job finished in 4m23s (219.6 s for the script), reusing the dataset already on the PVC. The loss fell from 2.225 to 1.267, and test accuracy was **52%**. It differs slightly from the deployment run because the weights start from a different random initialization and the data is shuffled differently. Log: `task2_nautilus/logs/job_train.log`. [Screenshot]

## Deployment vs. Job

A **deployment** keeps a pod running (and restarts it), which is good for interactive work but wastes a GPU if forgotten. A **job** runs a command to completion and then releases its resources, which is better for training runs. That's also why `sleep infinity` is fine in a deployment but never in a job.

## Issues / feedback

- The task says the namespace is joined "through Discord," but nothing tells you that the kubeconfig needs the separate `kubelogin` plugin. Without it, `kubectl` fails with an unclear error.
- Downloading CIFAR-10 inside the pod was very slow (about 95 KB/s, 30 minutes). Keeping the dataset on the PVC fixed this for later runs. A shared copy of the dataset in the namespace would save everyone the wait.
