"""
入口：多行业股票的自由现金流折现（DCF）现值对比。

干什么：
  1. 读知识体系「DCF估值 / 自由现金流」公式
  2. 拉取各行业龙头股近 N 年 FCF（经营现金流 − 购建固定资产）
  3. 用两阶段模型估算企业价值现值，并与市值对比
  4. 打印表格 + 生成 HTML

说明（教学简化）:
  - 折现对象是 FCFF 企业价值，未扣净债务，故「EV/市值」仅作量级对比
  - 银行/保险等金融业 FCF 口径特殊，结果仅供学习参考

运行：
    uv run python -m finance_lab.apps.dcf_sector_compare
    # 打开 finance_lab/output/dcf_sector_compare.html
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass

import pandas as pd

from finance_lab.core.dcf import (
    STOCK_PV_FORMULA,
    clip_growth,
    compute_fcff_dcf,
    historical_fcf_cagr,
    pick_base_fcf,
    yuan_to_yi,
)
from finance_lab.core.knowledge import find_term
from finance_lab.core.market_data import (
    fetch_annual_fcf,
    fetch_latest_price_and_shares,
    resolve_discount_rate,
)
from finance_lab.core.paths import OUTPUT_DIR
from finance_lab.core.samples import SECTOR_SAMPLES
from finance_lab.reports.dcf_compare import render_html


@dataclass
class DcfRow:
    sector: str
    name: str
    symbol: str
    base_fcf_yi: float
    hist_growth: float | None
    forecast_growth: float
    discount_rate: float
    stock_pv_yi: float  # 股票现值（亿元）
    market_cap_yi: float
    pv_over_mcap: float  # 股票现值 / 市值
    value_per_share: float
    market_price: float
    note: str


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="多行业 FCFF-DCF 现值对比")
    p.add_argument("--years", type=int, default=5, help="回看年度 FCF 年数")
    p.add_argument("--horizon", type=int, default=5, help="显性预测年数")
    p.add_argument("--r", type=float, default=None, help="折现率（小数），默认国债+溢价")
    p.add_argument("--erp", type=float, default=0.05, help="股权风险溢价，默认 5%")
    p.add_argument("--g", type=float, default=None, help="预测期增长率（小数），默认用历史 CAGR")
    p.add_argument("--g-term", type=float, default=0.02, help="永续增长率，默认 2%")
    return p


def analyze_one(
    item: dict,
    years: int,
    horizon: int,
    discount_rate: float,
    cli_g: float | None,
    g_term: float,
) -> DcfRow:
    fcf_df = fetch_annual_fcf(item["symbol"], years=years)
    series = fcf_df.set_index("year")["fcf"]
    base = pick_base_fcf(series)
    hist_g = historical_fcf_cagr(series)
    if cli_g is not None:
        g = clip_growth(cli_g)
    elif hist_g is not None:
        g = clip_growth(hist_g)
    else:
        g = 0.03  # 无法估计时用温和假设

    dcf = compute_fcff_dcf(
        base_fcf=base,
        discount_rate=discount_rate,
        forecast_growth=g,
        terminal_growth=g_term,
        explicit_years=horizon,
    )
    price, shares = fetch_latest_price_and_shares(item["symbol"])
    mcap = price * shares
    stock_pv = dcf.stock_present_value
    per_share = stock_pv / shares

    notes = []
    if item["sector"] in {"银行", "保险"}:
        notes.append("金融业FCF口径特殊")
    if base <= 0:
        notes.append("基准FCF非正，结果不稳定")
    if hist_g is None:
        notes.append("历史增速不可用，已用默认/指定g")

    return DcfRow(
        sector=item["sector"],
        name=item["name"],
        symbol=item["symbol"],
        base_fcf_yi=yuan_to_yi(base),
        hist_growth=hist_g,
        forecast_growth=g,
        discount_rate=discount_rate,
        stock_pv_yi=yuan_to_yi(stock_pv),
        market_cap_yi=yuan_to_yi(mcap),
        pv_over_mcap=stock_pv / mcap,
        value_per_share=per_share,
        market_price=price,
        note="；".join(notes) if notes else "",
    )


def to_table(rows: list[DcfRow]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(r) for r in rows]).rename(
        columns={
            "sector": "行业",
            "name": "名称",
            "symbol": "代码",
            "base_fcf_yi": "基准FCF(亿)",
            "hist_growth": "历史CAGR",
            "forecast_growth": "预测g",
            "discount_rate": "折现率r",
            "stock_pv_yi": "股票现值(亿)",
            "market_cap_yi": "市值(亿)",
            "pv_over_mcap": "现值/市值",
            "value_per_share": "模型每股价值",
            "market_price": "市价",
            "note": "备注",
        }
    )
    return df.sort_values("现值/市值", ascending=False).reset_index(drop=True)


def print_table(table: pd.DataFrame) -> None:
    show = table.copy()
    show["基准FCF(亿)"] = show["基准FCF(亿)"].map(lambda x: f"{x:,.1f}")
    show["历史CAGR"] = show["历史CAGR"].map(
        lambda x: "—" if x is None or (isinstance(x, float) and pd.isna(x)) else f"{x:.1%}"
    )
    show["预测g"] = show["预测g"].map(lambda x: f"{x:.1%}")
    show["折现率r"] = show["折现率r"].map(lambda x: f"{x:.2%}")
    show["股票现值(亿)"] = show["股票现值(亿)"].map(lambda x: f"{x:,.1f}")
    show["市值(亿)"] = show["市值(亿)"].map(lambda x: f"{x:,.1f}")
    show["现值/市值"] = show["现值/市值"].map(lambda x: f"{x:.2f}x")
    show["模型每股价值"] = show["模型每股价值"].map(lambda x: f"{x:.2f}")
    show["市价"] = show["市价"].map(lambda x: f"{x:.2f}")
    cols = [
        "行业",
        "名称",
        "基准FCF(亿)",
        "历史CAGR",
        "预测g",
        "折现率r",
        "股票现值(亿)",
        "市值(亿)",
        "现值/市值",
        "模型每股价值",
        "市价",
        "备注",
    ]
    print(show[cols].to_string(index=False))


def main() -> None:
    args = build_parser().parse_args()
    r, r_text = resolve_discount_rate(args.r, equity_premium=args.erp)

    print("知识体系 · DCF / 自由现金流")
    print(find_term("DCF估值").summary())
    print()
    print(find_term("自由现金流").summary())
    print()
    print(
        f"参数: 回看{args.years}年 FCF | 预测{args.horizon}年 | "
        f"r={r:.2%}（{r_text}）| g_term={args.g_term:.2%}"
    )
    print("拉取并估值…")

    rows: list[DcfRow] = []
    for item in SECTOR_SAMPLES:
        try:
            row = analyze_one(
                item,
                years=args.years,
                horizon=args.horizon,
                discount_rate=r,
                cli_g=args.g,
                g_term=args.g_term,
            )
            rows.append(row)
            print(
                f"  OK {item['sector']:4} {item['name']}: "
                f"现值={row.stock_pv_yi:,.1f}亿, "
                f"市值={row.market_cap_yi:,.1f}亿, "
                f"现值/市值={row.pv_over_mcap:.2f}x"
            )
        except Exception as e:
            print(f"  FAIL {item['sector']} {item['name']}: {e}")

    if not rows:
        raise SystemExit("全部样本估值失败")

    table = to_table(rows)
    print()
    print("=" * 96)
    print("股票现值对比（按 现值/市值 排序；>1 表示模型价值高于市值）")
    print(STOCK_PV_FORMULA)
    print("=" * 96)
    print_table(table)

    out = OUTPUT_DIR / "dcf_sector_compare.html"
    fcf_term = find_term("自由现金流")
    render_html(
        table=table,
        formula=(
            f"{STOCK_PV_FORMULA}\n"
            f"终值 = FCF_n × (1+g) / (r − g)\n"
            f"{fcf_term.name}: {fcf_term.formula}"
        ),
        r_text=r_text,
        g_term=args.g_term,
        horizon=args.horizon,
        out_path=out,
    )
    print()
    print(f"可视化: {out}")


if __name__ == "__main__":
    main()
