"""
入口：多行业龙头股风险收益对比。

干什么：
  - 白酒/银行/新能源/医药/保险/科技各行业若干龙头股
  - 同一时间段计算区间收益、年化收益、波动、夏普
  - 终端打印对比表，并生成 HTML（柱状图 + 归一化走势）

适合：看不同行业龙头在同一区间谁更「值」风险收益。

运行：
    uv run python -m finance_lab.apps.sector_compare
    # 打开 finance_lab/output/sector_compare.html
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass

import pandas as pd

from finance_lab.core.indicators import (
    compute_sharpe,
    normalized_price,
    total_return,
)
from finance_lab.core.knowledge import find_term
from finance_lab.core.market_data import fetch_a_share_daily, resolve_risk_free
from finance_lab.core.paths import OUTPUT_DIR
from finance_lab.core.samples import SECTOR_SAMPLES
from finance_lab.reports.sector_compare import render_html


@dataclass
class StockMetrics:
    sector: str
    name: str
    symbol: str
    total_return: float
    annual_return: float
    annual_volatility: float
    sharpe: float
    last_close: float
    n_days: int


def collect_metrics(
    samples: list[dict],
    start: str,
    end: str,
    risk_free: float,
) -> tuple[list[StockMetrics], pd.DataFrame]:
    rows: list[StockMetrics] = []
    curves: dict[str, pd.Series] = {}

    for item in samples:
        df = fetch_a_share_daily(item["symbol"], start, end)
        close = df["close"]
        sharpe = compute_sharpe(close, risk_free_annual=risk_free)
        label = f"{item['name']}({item['sector']})"
        nav = normalized_price(close)
        nav.index = pd.to_datetime(df["date"])
        curves[label] = nav

        rows.append(
            StockMetrics(
                sector=item["sector"],
                name=item["name"],
                symbol=item["symbol"],
                total_return=total_return(close),
                annual_return=sharpe.annual_return,
                annual_volatility=sharpe.annual_volatility,
                sharpe=sharpe.sharpe,
                last_close=float(close.iloc[-1]),
                n_days=sharpe.n_days,
            )
        )
        print(f"  OK {item['sector']:4} {item['name']}  夏普={sharpe.sharpe:+.3f}")

    return rows, pd.DataFrame(curves).sort_index().ffill(limit=3)


def metrics_to_table(rows: list[StockMetrics]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(r) for r in rows]).rename(
        columns={
            "sector": "行业",
            "name": "名称",
            "symbol": "代码",
            "total_return": "区间收益",
            "annual_return": "年化收益",
            "annual_volatility": "年化波动",
            "sharpe": "夏普比率",
            "last_close": "最新收盘",
            "n_days": "样本天数",
        }
    )
    return df.sort_values("夏普比率", ascending=False).reset_index(drop=True)


def print_table(table: pd.DataFrame) -> None:
    show = table.copy()
    for col in ("区间收益", "年化收益", "年化波动"):
        show[col] = show[col].map(lambda x: f"{x:.2%}")
    show["夏普比率"] = show["夏普比率"].map(lambda x: f"{x:+.3f}")
    show["最新收盘"] = show["最新收盘"].map(lambda x: f"{x:.2f}")
    print(show.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="多行业龙头股表格与图形对比")
    p.add_argument("--start", default="20240101")
    p.add_argument("--end", default="20260724")
    p.add_argument("--rf", type=float, default=None, help="年化无风险利率（小数）")
    return p


def main() -> None:
    args = build_parser().parse_args()
    rf, rf_text = resolve_risk_free(args.rf)

    print("知识体系 · 夏普比率")
    print(find_term("夏普比率").summary())
    print()
    print(f"区间 {args.start} → {args.end} | Rf: {rf_text}")
    print("拉取并计算各行业样本…")

    rows, curve_df = collect_metrics(SECTOR_SAMPLES, args.start, args.end, rf)
    table = metrics_to_table(rows)

    print()
    print("=" * 72)
    print("对比表（按夏普排序）")
    print("=" * 72)
    print_table(table)

    out = OUTPUT_DIR / "sector_compare.html"
    term = find_term("夏普比率")
    render_html(
        table=table,
        curve_df=curve_df,
        start=args.start,
        end=args.end,
        rf_text=rf_text,
        formula=term.formula or term.definition,
        out_path=out,
    )
    print()
    print(f"可视化已生成: {out}")


if __name__ == "__main__":
    main()
