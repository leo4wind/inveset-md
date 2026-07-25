"""从 AKShare 拉取行情等原始数据（优先较稳定的新浪接口）。"""

from __future__ import annotations

import akshare as ak
import pandas as pd


def fetch_a_share_daily(
    symbol: str,
    start_date: str,
    end_date: str,
    adjust: str = "qfq",
) -> pd.DataFrame:
    """
    拉取 A 股日线。

    symbol: 带市场前缀，如 sh600519、sz300750
    start_date / end_date: YYYYMMDD
    adjust: qfq=前复权, hfq=后复权, ""=不复权
    """
    df = ak.stock_zh_a_daily(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )
    if df is None or df.empty:
        raise RuntimeError(f"未取到日线: {symbol}")

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values("date").reset_index(drop=True)
    return out


def fetch_china_5y_yield_percent(as_of: str | None = None) -> float | None:
    """
    尝试读取中债国债 5 年收益率（单位：百分比，如 1.44 表示 1.44%）。

    失败时返回 None，由调用方使用默认无风险利率。
    """
    try:
        # 取近一段曲线，用最新「中债国债收益率曲线」的 5 年点
        end = as_of or pd.Timestamp.today().strftime("%Y%m%d")
        start = (pd.Timestamp(end) - pd.Timedelta(days=14)).strftime("%Y%m%d")
        curve = ak.bond_china_yield(start_date=start, end_date=end)
        if curve is None or curve.empty:
            return None
        mask = curve["曲线名称"].astype(str).str.contains("中债国债收益率曲线", na=False)
        rows = curve.loc[mask] if mask.any() else curve
        value = float(rows.iloc[-1]["5年"])
        return value
    except Exception:
        return None
