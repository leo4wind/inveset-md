"""多行业 DCF（股票现值）对比页的 HTML 渲染。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from finance_lab.core.paths import LAB_ROOT

FORMULA_IMAGE = LAB_ROOT / "assets" / "stock_pv_dcf_formula.png"


def render_html(
    table: pd.DataFrame,
    formula: str,
    r_text: str,
    g_term: float,
    horizon: int,
    out_path: Path,
) -> None:
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
    table_html = show[cols].to_html(index=False, classes="cmp", border=0, escape=True)

    labels = [f"{n}·{s}" for n, s in zip(table["名称"], table["行业"])]
    payload = {
        "labels": labels,
        "pv": [round(float(x), 1) for x in table["股票现值(亿)"]],
        "mcap": [round(float(x), 1) for x in table["市值(亿)"]],
        "ratio": [round(float(x), 2) for x in table["现值/市值"]],
    }

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>多行业股票现值（DCF）对比</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  body {{
    margin: 0; font-family: "PingFang SC", "Noto Sans SC", sans-serif;
    background: linear-gradient(165deg, #e8eef5, #f6f1e8 55%, #ebe6dc);
    color: #1c1917; line-height: 1.55;
  }}
  header, main {{ max-width: 1120px; margin: 0 auto; padding: 24px 28px; }}
  h1 {{ margin: 0 0 8px; font-size: 26px; }}
  .muted {{ color: #57534e; font-size: 14px; }}
  section {{
    background: #fffdf8; border: 1px solid #e7e5e4; border-radius: 14px;
    padding: 16px 18px; margin: 14px 0;
  }}
  h2 {{ margin: 0 0 10px; font-size: 16px; color: #0f766e; }}
  .formula {{
    background: #f5f5f4; border-left: 3px solid #0f766e;
    padding: 10px 12px; border-radius: 0 8px 8px 0; font-size: 13px;
    white-space: pre-wrap;
  }}
  .formula-img {{
    display: block; max-width: 100%; height: auto; margin: 12px 0 4px;
    border-radius: 8px; border: 1px solid #e7e5e4; background: #fff;
  }}
  table.cmp {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  table.cmp th, table.cmp td {{ padding: 8px 10px; border-bottom: 1px solid #e7e5e4; }}
  table.cmp th {{ color: #57534e; font-size: 12px; }}
  .charts {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
  .chart-box {{ height: 340px; position: relative; }}
  ul.note {{ margin: 8px 0 0; padding-left: 1.2em; font-size: 13px; color: #44403c; }}
</style>
</head>
<body>
<header>
  <h1>多行业股票现值（自由现金流折现）</h1>
  <p class="muted">
    预测期 {horizon} 年 · 永续 g={g_term:.2%} · 折现率：{r_text}
  </p>
</header>
<main>
  <section>
    <h2>计算公式</h2>
    <img class="formula-img" src="stock_pv_dcf_formula.png" alt="股票现值公式">
    <div class="formula">{formula}</div>
    <ul class="note">
      <li>左边「股票现值」= 预测期内各年自由现金流折现之和 + 终值折现</li>
      <li>FCF ≈ 经营现金流净额 − 购建固定资产等（CapEx）</li>
      <li>现值/市值 &gt; 1：模型价值高于当前市值（教学简化，未扣净债务）</li>
      <li>银行/保险等金融业现金流口径与实业不同，解读需谨慎</li>
    </ul>
  </section>

  <section>
    <h2>现值对比表</h2>
    {table_html}
  </section>

  <section>
    <h2>图形</h2>
    <div class="charts">
      <div class="chart-box"><canvas id="pvMcap"></canvas></div>
      <div class="chart-box"><canvas id="ratio"></canvas></div>
    </div>
  </section>
</main>
<script>
const d = {json.dumps(payload, ensure_ascii=False)};

new Chart(document.getElementById('pvMcap'), {{
  type: 'bar',
  data: {{
    labels: d.labels,
    datasets: [
      {{ label: '股票现值(亿)', data: d.pv, backgroundColor: 'rgba(15,118,110,0.75)' }},
      {{ label: '市值(亿)', data: d.mcap, backgroundColor: 'rgba(120,113,108,0.55)' }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ title: {{ display: true, text: '股票现值 vs 市值' }} }},
    scales: {{ y: {{ title: {{ display: true, text: '亿元' }} }} }}
  }}
}});

new Chart(document.getElementById('ratio'), {{
  type: 'bar',
  data: {{
    labels: d.labels,
    datasets: [{{
      label: '现值 / 市值',
      data: d.ratio,
      backgroundColor: d.ratio.map(v => v >= 1 ? 'rgba(15,118,110,0.75)' : 'rgba(180,83,9,0.7)')
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      title: {{ display: true, text: '现值/市值（绿≥1，橙&lt;1）' }},
      legend: {{ display: false }}
    }},
    scales: {{ y: {{ title: {{ display: true, text: '倍数' }}, suggestedMin: 0 }} }}
  }}
}});
</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    # 公式图放到 HTML 同目录，方便本地直接打开
    if FORMULA_IMAGE.exists():
        shutil.copy2(FORMULA_IMAGE, out_path.parent / FORMULA_IMAGE.name)
