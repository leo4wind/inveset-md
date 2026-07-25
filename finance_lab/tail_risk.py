"""
用真实日收益数据，检验「尾部风险」是否存在。

证明思路（对照正态假设）:
1. 超额峰度 > 0  → 分布比正态更「肥尾」
2. 偏度 < 0      → 左尾（大跌）更重
3. |收益| > 3σ / 5σ 的实际天数，远多于正态理论期望
4. 历史 VaR(95%) 与最大回撤：刻画已实现的极端损失

知识体系对应: 尾部风险、VaR、黑天鹅、回撤、波动率
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erfc, sqrt

import numpy as np
import pandas as pd


def _norm_two_tail_prob(z: float) -> float:
    """标准正态 P(|Z| >= z)。"""
    # 单侧生存函数 ≈ 0.5 * erfc(z / √2)
    return erfc(z / sqrt(2.0))


@dataclass(frozen=True)
class TailEvidence:
    name: str
    symbol: str
    n_days: int
    mean_daily: float
    std_daily: float
    skewness: float
    excess_kurtosis: float  # 正态约为 0；明显 >0 表示肥尾
    days_beyond_3sigma: int
    expected_3sigma_normal: float
    days_beyond_5sigma: int
    expected_5sigma_normal: float
    var_95: float  # 日度历史法；负值=亏损
    max_drawdown: float

    def proves_fat_tail(self) -> bool:
        """简单判据：超额峰度偏高，或 3σ 事件远超正态期望。"""
        return self.excess_kurtosis > 1.0 or (
            self.days_beyond_3sigma > max(2.0, 3 * self.expected_3sigma_normal)
        )


def max_drawdown(close: pd.Series) -> float:
    """最大回撤（正数比例，如 0.35 = 35%）。"""
    nav = close.astype(float)
    peak = nav.cummax()
    dd = (peak - nav) / peak
    return float(dd.max())


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

    skew = float(rets.skew())
    # pandas kurt = 超额峰度（Fisher），正态≈0
    ex_kurt = float(rets.kurt())

    z = (rets - mu) / sigma
    beyond_3 = int((z.abs() >= 3).sum())
    beyond_5 = int((z.abs() >= 5).sum())

    exp3 = n * _norm_two_tail_prob(3.0)
    exp5 = n * _norm_two_tail_prob(5.0)

    var_95 = float(np.quantile(rets, 0.05))

    evidence = TailEvidence(
        name=name,
        symbol=symbol,
        n_days=n,
        mean_daily=mu,
        std_daily=sigma,
        skewness=skew,
        excess_kurtosis=ex_kurt,
        days_beyond_3sigma=beyond_3,
        expected_3sigma_normal=float(exp3),
        days_beyond_5sigma=beyond_5,
        expected_5sigma_normal=float(exp5),
        var_95=var_95,
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
