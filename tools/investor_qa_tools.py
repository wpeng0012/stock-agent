from typing import Any, Dict

from services.research_source_runner import run_akshare_provider
from tools.research_common import normalize_stock_code, value_from


def fetch_investor_qa(
    stock_code: str,
    max_items: int = 50,
    timeout_seconds: int = 15,
) -> Dict[str, Any]:
    code = normalize_stock_code(stock_code)
    if code.startswith(("5", "6", "9")):
        return {
            "status": "unavailable",
            "provider": "stock_sns_sseinfo",
            "stock_code": code,
            "records": [],
            "returned": 0,
            "error": "当前上证e互动接口会全量翻页，V0.3暂不调用",
        }
    result = run_akshare_provider(
        "stock_irm_cninfo",
        {"symbol": code},
        timeout_seconds=timeout_seconds,
        max_records=max_items,
    )
    normalized = []
    for row in result.get("records", []):
        normalized.append({
            "stock_code": str(value_from(row, ("股票代码",)) or code).zfill(6),
            "stock_name": value_from(row, ("公司简称",)),
            "question": value_from(row, ("问题",)),
            "answer": value_from(row, ("回答内容", "回答")),
            "question_time": value_from(row, ("提问时间",)),
            "answer_time": value_from(row, ("回答时间",)),
            "source_name": "深交所互动易",
            "source_level": 2,
        })
    result["records"] = normalized
    result["stock_code"] = code
    return result
