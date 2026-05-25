# Target Server Environment

This project is currently delivered and validated for the A20CPolar server environment below. The portable `public-mini` demo remains useful as a smoke test, but the primary closed-loop research demo targets this server setup.

## Host

| Item | Value |
|---|---|
| Hostname | `xu` |
| OS | Ubuntu 22.04.5 LTS (`jammy`) |
| Kernel | `6.8.0-107-generic` |
| Home filesystem | `/home`, 807 GB total, 182 GB available at validation time |

## GPU

| Item | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 3090 |
| VRAM | 24,576 MiB |
| Driver | 570.211.01 |
| System CUDA | 12.8 |
| Compute capability | 8.6 |

## Python And Conda

| Purpose | Path | Version |
|---|---|---|
| Agent CLI environment | `/home/xu/anaconda3` | Python 3.12.12 |
| Time-Series-Library_simple backend | `/home/xu/anaconda3/envs/time_series_library` | Python 3.10.16 |

Relevant `time_series_library` packages observed during validation:

| Package | Version |
|---|---|
| PyTorch | `2.7.1+cu126` |
| PyTorch CUDA | `12.6` |
| NumPy | `2.2.6` |
| pandas | `2.2.3` |
| scikit-learn | `1.6.1` |
| matplotlib | `3.10.3` |

PyTorch CUDA check:

```text
torch_cuda_available=True
torch_gpu=NVIDIA GeForce RTX 3090
```

## Server Paths

| Asset | Path | Notes |
|---|---|---|
| Agent repo | `/home/xu/ts-auto-research-agent` | Public repo working copy |
| Paper notes | `/home/xu/autoresearch-agent/knowledge-base/paper-notes` | Read-only literature substrate |
| Time-Series-Library_simple | `/home/xu/pytorch_projects/my_time_series_lab/Time-Series-Library_simple` | Primary real experiment backend |
| TSFM_EVAL | `/home/xu/pytorch_projects/my_time_series_lab/TSFM_EVAL` | In active scope, not used by the current demo runner |
| TSL dataset | `/home/xu/pytorch_projects/my_time_series_lab/Time-Series-Library_simple/dataset/ETTh1.csv` | Used by the server demo through `ETTh1.csv` |

Active scope file:

```text
research_state/experiment_scope.json
```

Active scope name:

```text
general-ts-two-libs
```

Active baseline repositories:

```text
baseline_repo_tsfm_eval_2b0f29fb
baseline_repo_time_series_library_simple_d8b93a49
```

## Main Validation Command

```bash
cd /home/xu/ts-auto-research-agent
/home/xu/anaconda3/bin/python -m pip install -e .
ts-agent demo full-research
```

This command uses the server paper-note path, runs the Time-Series-Library_simple adapter, writes recoverable run artifacts, updates the leaderboard, and generates `research_state/full_research_demo_report.md`.
