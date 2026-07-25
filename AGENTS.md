# AGENTS.md — invest-md 项目目标与协作说明

## 我在做什么

本仓库服务个人金融学习与研究，核心有两块：

1. **金融投资知识体系**（`金融投资知识体系.json` + 可视化 HTML）  
   用结构化方式沉淀金融名词、分层框架、关系边，以及可阅读的公式说明（如夏普比率、CAPM、PE、ROE、折现等）。

2. **把知识体系「算出来」**（`finance_lab/`）  
   用 [AKShare](https://github.com/akfamily/akshare) 拉取真实金融产品数据（股票行情、利率等），  
   再对照知识体系里的 `formula`，用 Python 计算出数值结果，便于验证概念、做案例对比。

一句话：**知识体系负责「是什么 / 怎么算」；AKShare 负责「数据从哪来」；`finance_lab` 负责「算出结果」。**

## 技术选择（给 Agent 的约束）

- Python 环境用 **uv** + 项目 `.venv`，版本见 `.python-version`（当前 3.12）。
- 行情库安装 **PyPI 的 `akshare`**，不要再引入 AKTools，也不要默认 vendoring 上游源码。
- 东方财富类接口在本机网络可能失败；优先使用较稳定的数据源（如新浪日线 `stock_zh_a_daily`），并做好失败降级。
- 新增计算代码放在 **`finance_lab/`**，保持人类易读：清晰命名、短函数、少量必要注释，避免过度抽象。

## 常用入口

```bash
# 安装依赖
uv sync

# 演示：读「夏普比率」公式 + 拉茅台日线并计算
uv run python -m finance_lab.demo

# 换标的 / 区间
uv run python -m finance_lab.demo --symbol sz300750 --start 20240101 --end 20260724

# 多行业代表股对比（表格 + HTML 图）
uv run python -m finance_lab.compare_sectors
# 打开 finance_lab/output/sector_compare.html

# 用数据证明尾部风险（肥尾 / 极端日 vs 正态）
uv run python -m finance_lab.tail_risk_demo
# 打开 finance_lab/output/tail_risk_evidence.html
```

知识体系可视化（需本地静态服务，以便加载同目录 JSON）：

```bash
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000/金融投资知识体系_可视化.html
```

## Agent 工作时请注意

- 改指标逻辑时，尽量与 JSON 中对应节点的 `formula` 字段保持一致，并在输出里同时展示「公式说明」和「计算结果」。
- 不要把密钥、代理配置、本地日志、`.venv` 提交进仓库。
- 未明确要求时，不要把临时抓数结果、调试 JSON 写进仓库根目录。
