"""
用真实日收益数据，检验「尾部风险」是否存在。

对照正态假设：超额峰度、3σ/5σ 极端日频率、历史 VaR、最大回撤。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erfc, exp, pi, sqrt

import numpy as np
import pandas as pd


def _norm_two_tail_prob(z: float) -> float:
    """标准正态 P(|Z| >= z)。"""
    return erfc(z / sqrt(2.0))


@dataclass(frozen=True)
class TailEvidence:
    name: str
    symbol: str
    n_days: int
    mean_daily: float
    std_daily: float
    skewness: float
    excess_kurtosis: float
    days_beyond_3sigma: int
    expected_3sigma_normal: float
    days_beyond_5sigma: int
    expected_5sigma_normal: float
    var_95: float
    max_drawdown: float

    def proves_fat_tail(self) -> bool:
        return self.excess_kurtosis > 1.0 or (
            self.days_beyond_3sigma > max(2.0, 3 * self.expected_3sigma_normal)
        )


def max_drawdown(close: pd.Series) -> float:
    """最大回撤（正数比例）。"""
    nav = close.astype(float)
    peak = nav.cummax()
    return float(((peak - nav) / peak).max())


def analyze_tail_risk(
    close: pd.Series,
    name: str,
    symbol: str,
) -> tuple[TailEvidence, pd.Series]:
    """对收盘价做尾部风险检验，返回证据摘要 + 日收益率。"""
    rets = close.astype(float).pct_change().dropna()
    n = len(rets)
    mu = float(rets.mean())
    sigma = float(rets.std(ddof=1))
    if sigma == 0:
        raise ZeroDivisionError("波动率为 0，无法检验尾部")

    z = (rets - mu) / sigma
    beyond_3 = int((z.abs() >= 3).sum())
    beyond_5 = int((z.abs() >= 5).sum())

    evidence = TailEvidence(
        name=name,
        symbol=symbol,
        n_days=n,
        mean_daily=mu,
        std_daily=sigma,
        skewness=float(rets.skew()),
        excess_kurtosis=float(rets.kurt()),
        days_beyond_3sigma=beyond_3,
        expected_3sigma_normal=float(n * _norm_two_tail_prob(3.0)),
        days_beyond_5sigma=beyond_5,
        expected_5sigma_normal=float(n * _norm_two_tail_prob(5.0)),
        var_95=float(np.quantile(rets, 0.05)),
        max_drawdown=max_drawdown(close),
    )
    return evidence, rets


def evidence_to_row(e: TailEvidence) -> dict:
    ratio3 = (
        e.days_beyond_3sigma / e.expected_3sigma_normal
        if e.expected_3sigma_normal > 0
        else float("inf")
    )
    return {
        "名称": e.name,
        "代码": e.symbol,
        "样本天": e.n_days,
        "偏度": e.skewness,
        "超额峰度": e.excess_kurtosis,
        "实际|Z|≥3": e.days_beyond_3sigma,
        "正态期望|Z|≥3": e.expected_3sigma_normal,
        "实际/期望(3σ)": ratio3,
        "实际|Z|≥5": e.days_beyond_5sigma,
        "正态期望|Z|≥5": e.expected_5sigma_normal,
        "日VaR95%": e.var_95,
        "最大回撤": e.max_drawdown,
        "肥尾?": "是" if e.proves_fat_tail() else "否",
    }


def make_hist_payload(rets: pd.Series, name: str) -> dict:
    """实际日收益直方图 vs 同均值方差正态的期望频数。"""
    arr = rets.to_numpy(dtype=float)
    mu, sigma = float(arr.mean()), float(arr.std(ddof=1))
    counts, edges = np.histogram(arr, bins=41)
    centers = 0.5 * (edges[:-1] + edges[1:])
    width = float(edges[1] - edges[0])
    normal = [
        len(arr)
        * width
        * (1.0 / (sigma * sqrt(2 * pi)))
        * exp(-0.5 * ((c - mu) / sigma) ** 2)
        for c in centers
    ]
    return {
        "title": name,
        "bins": [f"{c:.2%}" for c in centers],
        "actual": [int(x) for x in counts],
        "normal": [round(float(x), 2) for x in normal],
    }
