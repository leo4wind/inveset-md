from pathlib import Path

# finance_lab/core/paths.py → 上两级是项目根
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = Path(__file__).resolve().parents[1]

KNOWLEDGE_JSON = PROJECT_ROOT / "金融投资知识体系.json"
OUTPUT_DIR = LAB_ROOT / "output"
