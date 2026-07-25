"""
对照知识体系公式，用行情序列计算指标。

约定：
- 输入价格为日线收盘价
- 年化时按 252 个交易日
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class SharpeResult:
    """夏普比率计算结果（便于打印）。"""

    sharpe: float
    annual_return: float
    annual_volatility: float
    risk_free_annual: float
    n_days: int

    def as_text(self) -> str:
        return (
            f"夏普比率 = {self.sharpe:.4f}\n"
            f"  年化收益 Rp = {self.annual_return:.2%}\n"
            f"  年化波动 σp = {self.annual_volatility:.2%}\n"
            f"  无风险利率 Rf = {self.risk_free_annual:.2%}\n"
            f"  样本交易日 = {self.n_days}"
        )


def daily_returns(close: pd.Series) -> pd.Series:
    """简单日收益率: r_t = P_t / P_{t-1} - 1"""
    return close.astype(float).pct_change().dropna()


def compute_sharpe(
    close: pd.Series,
    risk_free_annual: float = 0.02,
) -> SharpeResult:
    """
    夏普比率 = (Rp − Rf) ÷ σp

    - Rp、σp：由日收益年化得到
    - Rf：年化无风险利率（小数，如 0.02）
    """
    rets = daily_returns(close)
    if len(rets) < 5:
        raise ValueError("有效收益样本过少，无法计算夏普比率")

    # 日度无风险利率（按交易日均摊）
    rf_daily = risk_free_annual / TRADING_DAYS_PER_YEAR

    excess = rets - rf_daily
    # 年化：均值×252，波动×√252
    annual_return = float(rets.mean() * TRADING_DAYS_PER_YEAR)
    annual_vol = float(rets.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))

    if annual_vol == 0:
        raise ZeroDivisionError("波动率为 0，无法计算夏普比率")

    sharpe = (annual_return - risk_free_annual) / annual_vol

    return SharpeResult(
        sharpe=float(sharpe),
        annual_return=annual_return,
        annual_volatility=annual_vol,
        risk_free_annual=risk_free_annual,
        n_days=len(rets),
    )


def compute_pe(price: float, eps: float) -> float:
    """市盈率 PE = 股价 / EPS"""
    if eps == 0:
        raise ZeroDivisionError("EPS 为 0，无法计算市盈率")
    return float(price / eps)


def total_return(close: pd.Series) -> float:
    """区间总收益率: P_end / P_start - 1"""
    start = float(close.iloc[0])
    end = float(close.iloc[-1])
    if start == 0:
        raise ZeroDivisionError("期初价格为 0")
    return end / start - 1.0


def normalized_price(close: pd.Series, base: float = 100.0) -> pd.Series:
    """把价格归一化到同一起点，便于多股对比走势。"""
    start = float(close.iloc[0])
    if start == 0:
        raise ZeroDivisionError("期初价格为 0")
    return close.astype(float) / start * base
