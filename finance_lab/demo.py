"""
演示：读知识体系公式说明 → 拉一只 A 股日线 → 计算夏普比率。

运行（在项目根目录）:
    uv run python -m finance_lab.demo
    uv run python -m finance_lab.demo --symbol sh600519 --start 20240101 --end 20260724
"""

from __future__ import annotations

import argparse

from finance_lab.indicators import compute_sharpe
from finance_lab.knowledge import find_term
from finance_lab.market_data import fetch_a_share_daily, fetch_china_5y_yield_percent


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="知识体系公式 + AKShare 指标演示")
    p.add_argument("--symbol", default="sh600519", help="A股代码，默认贵州茅台 sh600519")
    p.add_argument("--start", default="20240101", help="开始日期 YYYYMMDD")
    p.add_argument("--end", default="20260724", help="结束日期 YYYYMMDD")
    p.add_argument(
        "--rf",
        type=float,
        default=None,
        help="年化无风险利率（小数）。不传则尝试国债5年，失败则用 0.02",
    )
    return p


def resolve_risk_free(cli_rf: float | None) -> tuple[float, str]:
    """决定 Rf，并说明来源。"""
    if cli_rf is not None:
        return cli_rf, "命令行 --rf"

    y5 = fetch_china_5y_yield_percent()
    if y5 is not None:
        return y5 / 100.0, f"中债国债5年收益率 {y5:.4f}%"

    return 0.02, "默认 2%（未能读取国债收益率）"


def main() -> None:
    args = build_parser().parse_args()

    print("=" * 60)
    print("1) 知识体系中的公式说明")
    print("=" * 60)
    term = find_term("夏普比率")
    print(term.summary())
    print()

    print("=" * 60)
    print("2) 拉取行情")
    print("=" * 60)
    prices = fetch_a_share_daily(args.symbol, args.start, args.end)
    print(f"标的: {args.symbol}")
    print(f"区间: {args.start} → {args.end}")
    print(f"交易日数: {len(prices)}")
    print(f"最新收盘: {float(prices['close'].iloc[-1]):.4f} @ {prices['date'].iloc[-1].date()}")
    print()

    print("=" * 60)
    print("3) 按公式计算")
    print("=" * 60)
    rf, rf_source = resolve_risk_free(args.rf)
    print(f"无风险利率来源: {rf_source}")
    result = compute_sharpe(prices["close"], risk_free_annual=rf)
    print(result.as_text())
    print()
    print("说明: 这是用真实行情按知识体系公式算出的数值，")
    print("      公式文本来自 金融投资知识体系.json，数据来自 AKShare。")


if __name__ == "__main__":
    main()
