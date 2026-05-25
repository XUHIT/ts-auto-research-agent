import torch
import torch.nn as nn
from models.DLinear import Model as DLinearModel


class Model(nn.Module):
    """Calendar-conditioned DLinear residual adapter.

    The model keeps DLinear as the forecasting anchor and learns a small future
    calendar residual from timestamp features. It tests whether horizon-known
    periodic context adds signal beyond pure historical value extrapolation.
    """

    def __init__(self, configs):
        super().__init__()
        self.task_name = configs.task_name
        if self.task_name in {"classification", "anomaly_detection", "imputation"}:
            self.pred_len = configs.seq_len
        else:
            self.pred_len = configs.pred_len
        self.channels = configs.enc_in
        hidden = max(8, min(64, getattr(configs, "d_model", 64)))
        self.anchor = DLinearModel(configs)
        self.calendar = nn.Sequential(
            nn.Linear(4, hidden),
            nn.GELU(),
            nn.Dropout(getattr(configs, "dropout", 0.1)),
            nn.Linear(hidden, self.channels),
        )
        self.scale = nn.Parameter(torch.tensor(0.05))
        nn.init.zeros_(self.calendar[-1].weight)
        nn.init.zeros_(self.calendar[-1].bias)

    def _calendar_residual(self, x_mark_dec, target):
        if x_mark_dec is None or x_mark_dec.size(-1) != 4:
            return torch.zeros_like(target)
        future_mark = x_mark_dec[:, -self.pred_len :, :].to(dtype=target.dtype, device=target.device)
        residual = self.calendar(future_mark)
        residual = residual - residual.mean(dim=1, keepdim=True)
        level = target.detach().std(dim=1, keepdim=True).clamp_min(1e-4)
        return self.scale * residual * level

    def forward(self, x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None):
        base = self.anchor(x_enc, x_mark_enc, x_dec, x_mark_dec, mask=mask)
        if self.task_name in {"long_term_forecast", "short_term_forecast"}:
            return base + self._calendar_residual(x_mark_dec, base)
        return base
