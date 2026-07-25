"""
入口：用数据证明「尾部风险 / 肥尾」存在。

干什么：
  - 对多行业龙头股统计超额峰度、3σ/5σ 极端日 vs 正态期望
  - 计算历史日 VaR(95%) 与最大回撤
  - 终端打印证据表，并生成 HTML（柱状图 + 直方图对比正态）

适合：回答「为什么不能只用正态波动率看风险」。

运行：
    uv run python -m finance_lab.apps.tail_risk_evidence
    # 打开 finance_lab/output/tail_risk_evidence.html
"""

from __future__ import annotations

import argparse

import pandas as pd

from finance_lab.core.knowledge import find_term
from finance_lab.core.market_data import fetch_a_share_daily
from finance_lab.core.paths import OUTPUT_DIR
from finance_lab.core.samples import SECTOR_SAMPLES
from finance_lab.core.tail_risk import (
    analyze_tail_risk,
    evidence_to_row,
    make_hist_payload,
)
from finance_lab.reports.tail_risk import render_html


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="尾部风险数据证明")
    p.add_argument("--start", default="20240101")
    p.add_argument("--end", default="20260724")
    return p


def print_table(df: pd.DataFrame) -> None:
    show = df.copy()
    show["偏度"] = show["偏度"].map(lambda x: f"{x:+.3f}")
    show["超额峰度"] = show["超额峰度"].map(lambda x: f"{x:+.2f}")
    show["正态期望|Z|≥3"] = show["正态期望|Z|≥3"].map(lambda x: f"{x:.2f}")
    show["实际/期望(3σ)"] = show["实际/期望(3σ)"].map(lambda x: f"{x:.1f}x")
    show["正态期望|Z|≥5"] = show["正态期望|Z|≥5"].map(lambda x: f"{x:.3f}")
    show["日VaR95%"] = show["日VaR95%"].map(lambda x: f"{x:.2%}")
    show["最大回撤"] = show["最大回撤"].map(lambda x: f"{x:.1%}")
    cols = [
        "名称",
        "行业",
        "超额峰度",
        "偏度",
        "实际|Z|≥3",
        "正态期望|Z|≥3",
        "实际/期望(3σ)",
        "实际|Z|≥5",
        "日VaR95%",
        "最大回撤",
        "肥尾?",
    ]
    print(show[cols].to_string(index=False))


def main() -> None:
    args = build_parser().parse_args()

    print(find_term("尾部风险").summary())
    print()
    print(f"区间 {args.start} → {args.end}")
    print("检验：超额峰度、3σ/5σ 极端日、VaR 与最大回撤\n")

    rows = []
    hist_payload = None
    best_kurt = -1e9
    for item in SECTOR_SAMPLES:
        df = fetch_a_share_daily(item["symbol"], args.start, args.end)
        evidence, rets = analyze_tail_risk(df["close"], item["name"], item["symbol"])
        row = evidence_to_row(evidence)
        row["行业"] = item["sector"]
        rows.append(row)
        print(
            f"  {item['sector']:4} {item['name']}: "
            f"超额峰度={evidence.excess_kurtosis:+.2f}, "
            f"3σ实际/期望="
            f"{evidence.days_beyond_3sigma / max(evidence.expected_3sigma_normal, 1e-9):.1f}x, "
            f"最大回撤={evidence.max_drawdown:.1%}"
        )
        if evidence.excess_kurtosis > best_kurt:
            best_kurt = evidence.excess_kurtosis
            hist_payload = make_hist_payload(rets, item["name"])

    assert hist_payload is not None
    table = pd.DataFrame(rows).sort_values("超额峰度", ascending=False)

    print()
    print("=" * 88)
    print("尾部风险证据表（按超额峰度排序）")
    print("=" * 88)
    print_table(table)

    fat = (table["肥尾?"] == "是").sum()
    print()
    print(
        f"结论: {fat}/{len(table)} 只样本满足肥尾判据；"
        "极端日频率显著高于正态 → 支持「尾部风险存在」。"
    )

    out = OUTPUT_DIR / "tail_risk_evidence.html"
    render_html(table, hist_payload, args.start, args.end, out)
    print(f"可视化: {out}")


if __name__ == "__main__":
    main()
