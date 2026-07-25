"""尾部风险证据页的 HTML 渲染。"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from finance_lab.core.knowledge import find_term


def render_html(
    table: pd.DataFrame,
    hist_payload: dict,
    start: str,
    end: str,
    out_path: Path,
) -> None:
    show = table.copy()
    show["偏度"] = show["偏度"].map(lambda x: f"{x:+.3f}")
    show["超额峰度"] = show["超额峰度"].map(lambda x: f"{x:+.2f}")
    show["正态期望|Z|≥3"] = show["正态期望|Z|≥3"].map(lambda x: f"{x:.2f}")
    show["实际/期望(3σ)"] = show["实际/期望(3σ)"].map(lambda x: f"{x:.1f}x")
    show["正态期望|Z|≥5"] = show["正态期望|Z|≥5"].map(lambda x: f"{x:.3f}")
    show["日VaR95%"] = show["日VaR95%"].map(lambda x: f"{x:.2%}")
    show["最大回撤"] = show["最大回撤"].map(lambda x: f"{x:.1%}")
    table_html = show[
        [
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
    ].to_html(index=False, classes="cmp", border=0, escape=True)

    term = find_term("尾部风险")
    var_term = find_term("VaR")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>尾部风险：数据证明</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  body {{
    margin: 0; font-family: "PingFang SC", "Noto Sans SC", sans-serif;
    background: linear-gradient(165deg, #eef2f7, #f7f3ea 50%, #ebe4d8);
    color: #1c1917; line-height: 1.55;
  }}
  header, main {{ max-width: 1100px; margin: 0 auto; padding: 24px 28px; }}
  h1 {{ margin: 0 0 8px; font-size: 26px; }}
  .muted {{ color: #57534e; font-size: 14px; }}
  section {{
    background: #fffdf8; border: 1px solid #e7e5e4; border-radius: 14px;
    padding: 16px 18px; margin: 14px 0;
  }}
  h2 {{ margin: 0 0 10px; font-size: 16px; color: #9a3412; }}
  .formula {{
    background: #f5f5f4; border-left: 3px solid #9a3412;
    padding: 10px 12px; border-radius: 0 8px 8px 0; font-size: 13px;
    white-space: pre-wrap;
  }}
  table.cmp {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  table.cmp th, table.cmp td {{ padding: 8px 10px; border-bottom: 1px solid #e7e5e4; }}
  table.cmp th {{ color: #57534e; font-size: 12px; }}
  .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .chart-box {{ height: 320px; position: relative; }}
  .chart-wide {{ grid-column: 1 / -1; height: 360px; }}
  ul.proof {{ margin: 8px 0 0; padding-left: 1.2em; font-size: 14px; }}
  @media (max-width: 860px) {{ .charts {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>如何用数据证明尾部风险</h1>
  <p class="muted">区间 {start} → {end} · 若收益服从正态，极端日应极少；现实往往多得多。</p>
</header>
<main>
  <section>
    <h2>知识体系</h2>
    <div class="formula"><b>{term.name}</b>：{term.definition}

VaR：{var_term.definition}
{var_term.formula}</div>
  </section>

  <section>
    <h2>证明逻辑</h2>
    <ul class="proof">
      <li><b>超额峰度 &gt; 0</b>：尾巴比正态分布更厚（肥尾）。</li>
      <li><b>实际 |Z|≥3 天数 ≫ 正态期望</b>：三倍标准差外的大跌/大涨远比理论频繁。</li>
      <li><b>|Z|≥5 仍出现</b>：正态下几乎不应发生，却在样本里出现 → 黑天鹅并非「不可能」。</li>
      <li><b>最大回撤 / 日 VaR</b>：把尾部风险落成已实现损失数字。</li>
    </ul>
  </section>

  <section>
    <h2>多行业证据表</h2>
    {table_html}
  </section>

  <section>
    <h2>图形</h2>
    <div class="charts">
      <div class="chart-box"><canvas id="kurtChart"></canvas></div>
      <div class="chart-box"><canvas id="ratioChart"></canvas></div>
      <div class="chart-box chart-wide"><canvas id="histChart"></canvas></div>
    </div>
  </section>
</main>
<script>
const table = {json.dumps({
    "names": table["名称"].tolist(),
    "kurt": [round(float(x), 2) for x in table["超额峰度"]],
    "ratio3": [round(float(x), 2) for x in table["实际/期望(3σ)"]],
}, ensure_ascii=False)};
const hist = {json.dumps(hist_payload, ensure_ascii=False)};

new Chart(document.getElementById('kurtChart'), {{
  type: 'bar',
  data: {{
    labels: table.names,
    datasets: [{{
      label: '超额峰度（正态≈0）',
      data: table.kurt,
      backgroundColor: 'rgba(154,52,18,0.75)'
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ title: {{ display: true, text: '超额峰度：越高越肥尾' }} }},
    scales: {{ y: {{ title: {{ display: true, text: '超额峰度' }} }} }}
  }}
}});

new Chart(document.getElementById('ratioChart'), {{
  type: 'bar',
  data: {{
    labels: table.names,
    datasets: [{{
      label: '实际/期望 (|Z|≥3)',
      data: table.ratio3,
      backgroundColor: 'rgba(15,118,110,0.75)'
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      title: {{ display: true, text: '极端日：实际是正态期望的多少倍' }},
      annotation: undefined
    }},
    scales: {{ y: {{ title: {{ display: true, text: '倍数' }}, suggestedMin: 0 }} }}
  }}
}});

new Chart(document.getElementById('histChart'), {{
  type: 'bar',
  data: {{
    labels: hist.bins,
    datasets: [
      {{
        label: '实际日收益分布',
        data: hist.actual,
        backgroundColor: 'rgba(154,52,18,0.55)',
        yAxisID: 'y'
      }},
      {{
        type: 'line',
        label: '若服从正态的期望频数',
        data: hist.normal,
        borderColor: '#0f766e',
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: 'y'
      }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      title: {{ display: true, text: hist.title + '：直方图 vs 正态（尾部抬升=肥尾）' }}
    }},
    scales: {{
      y: {{ title: {{ display: true, text: '天数' }} }},
      x: {{ ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 12 }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
