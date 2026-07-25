"""
分析用的默认股票样本：各行业若干龙头股。

symbol 使用新浪前缀（sh/sz），供 AKShare 日线与东财报表转换使用。
"""

from __future__ import annotations

# 行业 → 龙头股列表（约 2～3 只 / 行业）
SECTOR_LEADERS: dict[str, list[dict[str, str]]] = {
    "白酒": [
        {"name": "贵州茅台", "symbol": "sh600519"},
        {"name": "五粮液", "symbol": "sz000858"},
        {"name": "泸州老窖", "symbol": "sz000568"},
    ],
    "银行": [
        {"name": "招商银行", "symbol": "sh600036"},
        {"name": "兴业银行", "symbol": "sh601166"},
        {"name": "宁波银行", "symbol": "sz002142"},
    ],
    "新能源": [
        {"name": "宁德时代", "symbol": "sz300750"},
        {"name": "比亚迪", "symbol": "sz002594"},
        {"name": "阳光电源", "symbol": "sz300274"},
    ],
    "医药": [
        {"name": "恒瑞医药", "symbol": "sh600276"},
        {"name": "药明康德", "symbol": "sh603259"},
        {"name": "迈瑞医疗", "symbol": "sz300760"},
    ],
    "保险": [
        {"name": "中国平安", "symbol": "sh601318"},
        {"name": "中国人寿", "symbol": "sh601628"},
        {"name": "中国太保", "symbol": "sh601601"},
    ],
    "科技": [
        {"name": "海康威视", "symbol": "sz002415"},
        {"name": "立讯精密", "symbol": "sz002475"},
        {"name": "中兴通讯", "symbol": "sz000063"},
    ],
}

# 扁平列表：供对比 / 尾部风险 / DCF 等入口统一遍历
SECTOR_SAMPLES: list[dict[str, str]] = [
    {"sector": sector, "name": stock["name"], "symbol": stock["symbol"]}
    for sector, stocks in SECTOR_LEADERS.items()
    for stock in stocks
]


def sectors() -> list[str]:
    """行业名称列表（固定顺序）。"""
    return list(SECTOR_LEADERS.keys())


def leaders_in(sector: str) -> list[dict[str, str]]:
    """某行业的龙头股（带 sector 字段）。"""
    return [
        {"sector": sector, "name": s["name"], "symbol": s["symbol"]}
        for s in SECTOR_LEADERS[sector]
    ]
