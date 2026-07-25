"""
多行业代表股对比：表格 + 可视化 HTML。

默认样本（各选一只）:
  白酒 / 银行 / 新能源 / 医药 / 保险 / 科技

运行:
    uv run python -m finance_lab.compare_sectors
    uv run python -m finance_lab.compare_sectors --start 20240101 --end 20260724
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from finance_lab.indicators import (
    compute_sharpe,
    normalized_price,
    total_return,
)
from finance_lab.knowledge import find_term
from finance_lab.market_data import fetch_a_share_daily, fetch_china_5y_yield_percent
from finance_lab.paths import PROJECT_ROOT


# 各行业一只代表性 A 股（代码用新浪前缀）
SECTOR_SAMPLES = [
    {"sector": "白酒", "name": "贵州茅台", "symbol": "sh600519"},
    {"sector": "银行", "name": "招商银行", "symbol": "sh600036"},
    {"sector": "新能源", "name": "宁德时代", "symbol": "sz300750"},
    {"sector": "医药", "name": "恒瑞医药", "symbol": "sh600276"},
    {"sector": "保险", "name": "中国平安", "symbol": "sh601318"},
    {"sector": "科技", "name": "海康威视", "symbol": "sz002415"},
]

OUTPUT_DIR = PROJECT_ROOT / "finance_lab" / "output"


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


def resolve_risk_free(cli_rf: float | None) -> tuple[float, str]:
    if cli_rf is not None:
        return cli_rf, "命令行 --rf"
    y5 = fetch_china_5y_yield_percent()
    if y5 is not None:
        return y5 / 100.0, f"中债国债5年 {y5:.4f}%"
    return 0.02, "默认 2%"


def collect_metrics(
    samples: list[dict],
    start: str,
    end: str,
    risk_free: float,
) -> tuple[list[StockMetrics], pd.DataFrame]:
    """拉取各股并计算指标；同时返回归一化净值表（列=股票名）。"""
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

    # 对齐交易日，缺失向前填一点再插值不合适；用外连接后 ffill 有限
    curve_df = pd.DataFrame(curves).sort_index().ffill(limit=3)
    return rows, curve_df


def metrics_to_table(rows: list[StockMetrics]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(r) for r in rows])
    df = df.rename(
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


def render_html(
    table: pd.DataFrame,
    curve_df: pd.DataFrame,
    start: str,
    end: str,
    rf_text: str,
    formula: str,
    out_path: Path,
) -> None:
    """生成带表格 + 柱状图 + 归一化走势图的单页 HTML。"""
    # 表格用原始数值格式化
    display = table.copy()
    for col in ("区间收益", "年化收益", "年化波动"):
        display[col] = display[col].map(lambda x: f"{x:.2%}")
    display["夏普比率"] = display["夏普比率"].map(lambda x: f"{x:+.3f}")
    display["最新收盘"] = display["最新收盘"].map(lambda x: f"{x:.2f}")
    table_html = display.to_html(index=False, classes="cmp", border=0, escape=True)

    labels = table["名称"].tolist()
    sectors = table["行业"].tolist()
    chart_labels = [f"{n}·{s}" for n, s in zip(labels, sectors)]

    bar_payload = {
        "labels": chart_labels,
        "sharpe": [round(float(x), 4) for x in table["夏普比率"]],
        "annual_return": [round(float(x) * 100, 2) for x in table["年化收益"]],
        "annual_vol": [round(float(x) * 100, 2) for x in table["年化波动"]],
    }

    # 走势：降采样，避免点过多
    curve = curve_df.copy()
    if len(curve) > 400:
        step = max(1, len(curve) // 400)
        curve = curve.iloc[::step]
    line_payload = {
        "dates": [d.strftime("%Y-%m-%d") for d in curve.index],
        "series": [
            {"name": col, "data": [None if pd.isna(v) else round(float(v), 2) for v in curve[col]]}
            for col in curve.columns
        ],
    }

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>多行业代表股对比</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #f4f1ea;
    --ink: #1c1917;
    --muted: #57534e;
    --panel: #fffdf8;
    --line: #e7e5e4;
    --accent: #0f766e;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: "PingFang SC", "Noto Sans SC", sans-serif;
    background: linear-gradient(160deg, #efe8dc 0%, #f7f4ee 45%, #e8eef0 100%);
    color: var(--ink); line-height: 1.55;
  }}
  header {{
    padding: 28px 32px 10px; max-width: 1100px; margin: 0 auto;
  }}
  header h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0.02em; }}
  header p {{ margin: 0; color: var(--muted); font-size: 14px; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 12px 32px 48px; }}
  .meta {{ margin: 14px 0 22px; font-size: 13px; color: var(--muted); }}
  .meta code {{ background: #e7e5e4; padding: 1px 6px; border-radius: 4px; }}
  section {{
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 14px; padding: 18px 20px; margin-bottom: 18px;
  }}
  section h2 {{ margin: 0 0 12px; font-size: 17px; color: var(--accent); }}
  table.cmp {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  table.cmp th, table.cmp td {{
    padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left;
  }}
  table.cmp th {{ color: var(--muted); font-weight: 600; font-size: 12px; }}
  .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
  .chart-box {{ position: relative; height: 320px; }}
  .chart-wide {{ grid-column: 1 / -1; height: 380px; }}
  @media (max-width: 860px) {{
    .charts {{ grid-template-columns: 1fr; }}
    header, main {{ padding-left: 16px; padding-right: 16px; }}
  }}
  .formula {{
    font-size: 13px; background: #f5f5f4; border-left: 3px solid var(--accent);
    padding: 10px 12px; border-radius: 0 8px 8px 0; white-space: pre-wrap;
  }}
</style>
</head>
<body>
<header>
  <h1>多行业代表股对比</h1>
  <p>白酒 / 银行 / 新能源 / 医药 / 保险 / 科技 · 同一区间风险收益对比</p>
</header>
<main>
  <div class="meta">
    区间 <code>{start}</code> → <code>{end}</code>
    · 无风险利率：{rf_text}
    · 数据：AKShare 新浪日线（前复权）
  </div>

  <section>
    <h2>知识体系公式</h2>
    <div class="formula">{formula}</div>
  </section>

  <section>
    <h2>指标对比表（按夏普比率排序）</h2>
    {table_html}
  </section>

  <section>
    <h2>图形对比</h2>
    <div class="charts">
      <div class="chart-box"><canvas id="sharpeChart"></canvas></div>
      <div class="chart-box"><canvas id="retVolChart"></canvas></div>
      <div class="chart-box chart-wide"><canvas id="navChart"></canvas></div>
    </div>
  </section>
</main>
<script>
const bar = {json.dumps(bar_payload, ensure_ascii=False)};
const line = {json.dumps(line_payload, ensure_ascii=False)};

new Chart(document.getElementById('sharpeChart'), {{
  type: 'bar',
  data: {{
    labels: bar.labels,
    datasets: [{{
      label: '夏普比率',
      data: bar.sharpe,
      backgroundColor: bar.sharpe.map(v => v >= 0 ? 'rgba(15,118,110,0.75)' : 'rgba(180,83,9,0.7)')
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ title: {{ display: true, text: '夏普比率对比' }}, legend: {{ display: false }} }},
    scales: {{ y: {{ title: {{ display: true, text: '夏普' }} }} }}
  }}
}});

new Chart(document.getElementById('retVolChart'), {{
  type: 'bar',
  data: {{
    labels: bar.labels,
    datasets: [
      {{ label: '年化收益(%)', data: bar.annual_return, backgroundColor: 'rgba(15,118,110,0.7)' }},
      {{ label: '年化波动(%)', data: bar.annual_vol, backgroundColor: 'rgba(120,113,108,0.55)' }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ title: {{ display: true, text: '年化收益 vs 年化波动' }} }},
    scales: {{ y: {{ title: {{ display: true, text: '%' }} }} }}
  }}
}});

new Chart(document.getElementById('navChart'), {{
  type: 'line',
  data: {{
    labels: line.dates,
    datasets: line.series.map((s, i) => ({{
      label: s.name,
      data: s.data,
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.15
    }}))
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{ title: {{ display: true, text: '归一化走势（起点=100）' }} }},
    scales: {{
      y: {{ title: {{ display: true, text: '净值' }} }},
      x: {{ ticks: {{ maxTicksLimit: 8 }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="多行业代表股表格与图形对比")
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
    print("可用浏览器打开该文件；或: python3 -m http.server 8000 --directory finance_lab/output")


if __name__ == "__main__":
    main()
