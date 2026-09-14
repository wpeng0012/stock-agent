from typing import Any, Dict, Optional

from services.research_source_runner import run_akshare_provider
from tools.research_common import normalize_date, normalize_stock_code, value_from


def fetch_announcements(
    stock_code: str,
    start_date: str,
    end_date: str,
    category: str = "",
    max_items: int = 50,
    timeout_seconds: int = 15,
) -> Dict[str, Any]:
    code = normalize_stock_code(stock_code)
    start = normalize_date(start_date, "start_date")
    end = normalize_date(end_date, "end_date")
    if start > end:
        raise ValueError("start_date不能晚于end_date")

    result = run_akshare_provider(
        "stock_zh_a_disclosure_report_cninfo",
        {
            "symbol": code,
            "market": "沪深京",
            "keyword": "",
            "category": category,
            "start_date": start.replace("-", ""),
            "end_date": end.replace("-", ""),
        },
        timeout_seconds=timeout_seconds,
        max_records=max_items,
    )
    normalized = []
    for row in result.get("records", []):
        normalized.append({
            "stock_code": str(value_from(row, ("代码",)) or code).zfill(6),
            "stock_name": value_from(row, ("简称",)),
            "title": value_from(row, ("公告标题",)),
            "published_at": value_from(row, ("公告时间",)),
            "source_name": "巨潮资讯",
            "source_level": 1,
            "source_url": value_from(row, ("公告链接",)),
            "category": category or None,
        })
    result["records"] = normalized
    result["stock_code"] = code
    return result
