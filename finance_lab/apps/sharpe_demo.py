"""
入口：单只股票的夏普比率演示。

干什么：
  1. 从知识体系读出「夏普比率」的定义与公式
  2. 用 AKShare 拉一只 A 股日线
  3. 按公式算出数值并打印

适合：第一次验证「知识体系公式 ↔ 真实行情」链路是否通。

运行：
    uv run python -m finance_lab.apps.sharpe_demo
    uv run python -m finance_lab.apps.sharpe_demo --symbol sz300750 --start 20240101 --end 20260724
"""

from __future__ import annotations

import argparse

from finance_lab.core.indicators import compute_sharpe
from finance_lab.core.knowledge import find_term
from finance_lab.core.market_data import fetch_a_share_daily, resolve_risk_free


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="单票夏普比率演示（知识体系 + AKShare）")
    p.add_argument("--symbol", default="sh600519", help="A股代码，默认贵州茅台")
    p.add_argument("--start", default="20240101", help="开始日期 YYYYMMDD")
    p.add_argument("--end", default="20260724", help="结束日期 YYYYMMDD")
    p.add_argument("--rf", type=float, default=None, help="年化无风险利率（小数）")
    return p


def main() -> None:
    args = build_parser().parse_args()

    print("=" * 60)
    print("1) 知识体系中的公式说明")
    print("=" * 60)
    print(find_term("夏普比率").summary())
    print()

    print("=" * 60)
    print("2) 拉取行情")
    print("=" * 60)
    prices = fetch_a_share_daily(args.symbol, args.start, args.end)
    print(f"标的: {args.symbol}")
    print(f"区间: {args.start} → {args.end}")
    print(f"交易日数: {len(prices)}")
    print(
        f"最新收盘: {float(prices['close'].iloc[-1]):.4f} "
        f"@ {prices['date'].iloc[-1].date()}"
    )
    print()

    print("=" * 60)
    print("3) 按公式计算")
    print("=" * 60)
    rf, rf_source = resolve_risk_free(args.rf)
    print(f"无风险利率来源: {rf_source}")
    print(compute_sharpe(prices["close"], risk_free_annual=rf).as_text())
    print()
    print("说明: 公式文本来自 金融投资知识体系.json，数据来自 AKShare。")


if __name__ == "__main__":
    main()
