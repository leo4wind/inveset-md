"""多行业对比页的 HTML 渲染。"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


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
<title>多行业龙头股对比</title>
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
  <h1>多行业龙头股对比</h1>
  <p>白酒 / 银行 / 新能源 / 医药 / 保险 / 科技 · 各行业若干龙头 · 同一区间风险收益对比</p>
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
