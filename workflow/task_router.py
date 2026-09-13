import re
from typing import Any, Dict


TASK_TYPES = {
    "screen": "全市场筛选",
    "stock_query": "指定个股查询",
}

EXPLAIN_WORDS = (
    "为什么",
    "原因",
    "解释",
    "依据",
    "得分",
    "评分",
)

QUERY_WORDS = (
    "查询",
    "查看",
    "分析",
    "表现",
    "指标",
    "这只",
    "个股",
)

SCREEN_WORDS = (
    "筛选",
    "选股",
    "候选",
    "全市场",
    "股票池",
)


def extract_stock_code(query: str):
    matches = re.findall(r"(?<!\d)(?:[036]\d{5})(?!\d)", query)
    return matches[0] if matches else None


def classify_task(query: str) -> Dict[str, Any]:
    """识别V0.2支持的任务类型，不执行数据查询。"""
    text = (query or "").strip()
    if not text:
        return {
            "task_type": "screen",
            "task_name": TASK_TYPES["screen"],
            "stock_code": None,
            "stock_name": None,
            "explain": False,
            "status": "ready",
        }

    code = extract_stock_code(text)
    has_query_word = any(word in text for word in QUERY_WORDS)
    has_screen_word = any(word in text for word in SCREEN_WORDS)
    explain = any(word in text for word in EXPLAIN_WORDS)

    # 出现股票代码或明确的个股查询词时，走个股路径。
    is_stock_query = bool(code or (has_query_word and not has_screen_word))

    if is_stock_query:
        task_type = "stock_query"
    else:
        task_type = "screen"

    return {
        "task_type": task_type,
        "task_name": TASK_TYPES[task_type],
        "stock_code": code,
        "stock_name": None,
        "explain": explain,
        "status": "ready",
    }
