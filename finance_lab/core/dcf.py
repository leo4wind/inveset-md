"""
自由现金流折现（DCF）核心计算。

公式（股票现值）:
  股票现值 = Σ_{t=1..n} 未来第t年自由现金流 / (1+折现率)^t
           + 终值 / (1+折现率)^n

  其中终值 TV = FCF_n × (1+g) / (r - g)
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# 与示意图一致的公式文案（用于报告展示）
STOCK_PV_FORMULA = (
    "股票现值 = Σ_{t=1}^{n} [未来第 t 年的自由现金流 / (1+折现率)^t] "
    "+ 终值 / (1+折现率)^n"
)


@dataclass(frozen=True)
class DcfResult:
    """一只股票按上式算出的现值（教学简化版）。"""

    base_fcf: float  # 基准年自由现金流（元）
    forecast_growth: float  # 显性预测期增长率 g
    terminal_growth: float  # 永续增长率
    discount_rate: float  # 折现率 r
    explicit_years: int
    stock_present_value: float  # 股票现值（公式左边）
    terminal_value_pv: float  # 终值的现值
    explicit_pv: float  # 预测期 FCF 现值之和
    projected_fcfs: tuple[float, ...]  # FCF_1 … FCF_n

    @property
    def enterprise_value(self) -> float:
        """兼容旧字段名：此处与股票现值同一结果（未扣净债务的简化模型）。"""
        return self.stock_present_value


def historical_fcf_cagr(fcf_series: pd.Series) -> float | None:
    """
    用首尾正 FCF 估算历史复合增速；样本不足或非正则返回 None。
    fcf_series: 按时间升序的年度 FCF。
    """
    s = fcf_series.dropna().astype(float)
    if len(s) < 2:
        return None
    first, last = float(s.iloc[0]), float(s.iloc[-1])
    if first <= 0 or last <= 0:
        return None
    n = len(s) - 1
    return float((last / first) ** (1 / n) - 1)


def pick_base_fcf(fcf_series: pd.Series) -> float:
    """
    选预测起点：优先最近一年；若为负，则用近三年正值平均；仍不行用近三年平均。
    """
    s = fcf_series.dropna().astype(float)
    if s.empty:
        raise ValueError("没有可用的年度 FCF")
    latest = float(s.iloc[-1])
    if latest > 0:
        return latest
    recent = s.tail(3)
    positive = recent[recent > 0]
    if not positive.empty:
        return float(positive.mean())
    return float(recent.mean())


def clip_growth(g: float, low: float = -0.05, high: float = 0.15) -> float:
    """把增长率限制在合理教学区间，避免爆炸估值。"""
    return float(min(high, max(low, g)))


def compute_fcff_dcf(
    base_fcf: float,
    discount_rate: float,
    forecast_growth: float,
    terminal_growth: float,
    explicit_years: int = 5,
) -> DcfResult:
    """
    两阶段 FCFF 折现。

    - 预测期: FCF_t = base_fcf * (1+g)^t , t=1..n
    - 终值: TV = FCF_n * (1+g_term) / (r - g_term)
    - EV = Σ FCF_t/(1+r)^t + TV/(1+r)^n
    """
    r = discount_rate
    g = forecast_growth
    g_term = terminal_growth
    n = explicit_years

    if n < 1:
        raise ValueError("explicit_years 至少为 1")
    if r <= g_term:
        raise ValueError(f"折现率 r={r:.4f} 必须大于永续增长率 g={g_term:.4f}")

    projected = []
    explicit_pv = 0.0
    for t in range(1, n + 1):
        fcf_t = base_fcf * ((1 + g) ** t)
        projected.append(float(fcf_t))
        explicit_pv += fcf_t / ((1 + r) ** t)

    fcf_n = projected[-1]
    tv = fcf_n * (1 + g_term) / (r - g_term)
    tv_pv = tv / ((1 + r) ** n)
    # 股票现值 = 各年自由现金流折现之和 + 终值折现
    stock_pv = explicit_pv + tv_pv

    return DcfResult(
        base_fcf=float(base_fcf),
        forecast_growth=float(g),
        terminal_growth=float(g_term),
        discount_rate=float(r),
        explicit_years=n,
        stock_present_value=float(stock_pv),
        terminal_value_pv=float(tv_pv),
        explicit_pv=float(explicit_pv),
        projected_fcfs=tuple(projected),
    )


def yuan_to_yi(x: float) -> float:
    """元 → 亿元。"""
    return float(x) / 1e8
