# Time-Series-Library_simple Integration Notes

This folder contains the current benchmark candidate model used by the server demo.

## CalDLinear

`models/CalDLinear.py` is a lightweight candidate for Time-Series-Library_simple. It keeps DLinear as the forecasting anchor and adds a small future-calendar residual from known timestamp features.

Research role:

- `DLinear`: baseline anchor.
- `PatchTST`: strong reference.
- `CalDLinear`: literature-grounded innovation candidate.

Current validated result on ETTh1, `seq_len=24`, `pred_len=24`, `subset_ratio=0.05`, `train_epochs=3`:

| Model | Role | RMSE | MAE | Delta vs DLinear |
|---|---|---:|---:|---:|
| DLinear | baseline anchor | 0.59827763 | 0.38131171 | 0.00000000 |
| PatchTST | strong reference | 0.58627319 | 0.37807289 | +0.01200444 |
| CalDLinear | innovation candidate | 0.59605795 | 0.38774657 | +0.00221968 |

Interpretation: CalDLinear clears DLinear on RMSE but does not clear PatchTST, so it is a bounded candidate requiring ablations and broader validation.

## Applying To Time-Series-Library_simple

Copy `models/CalDLinear.py` into the external Time-Series-Library_simple `models/` folder and register `CalDLinear` in that repository's model import and `model_dict`. The server working tree already has this registration for the validated run.
