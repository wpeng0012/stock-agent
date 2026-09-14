from typing import Any, Dict

from services.research_source_runner import run_akshare_provider
from tools.research_common import normalize_date, normalize_stock_code, sort_and_limit, value_from


def fetch_unlock_events(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
    max_items: int = 20,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    code = normalize_stock_code(stock_code)
    start = normalize_date(start_date, "start_date")
    end = normalize_date(end_date, "end_date")
    result = run_akshare_provider(
        "stock_restricted_release_queue_em",
        {"symbol": code},
        timeout_seconds=timeout_seconds,
        max_records=max_items,
    )
    normalized = []
    for row in result.get("records", []):
        event = {
            "stock_code": code,
            "event_type": "share_unlock",
            "event_date": value_from(row, ("解禁时间",)),
            "shareholder_count": value_from(row, ("解禁股东数",)),
            "unlock_shares": value_from(row, ("解禁数量",)),
            "actual_unlock_shares": value_from(row, ("实际解禁数量",)),
            "actual_unlock_value": value_from(row, ("实际解禁数量市值",)),
            "market_cap_ratio": value_from(row, ("占总市值比例",)),
            "float_cap_ratio": value_from(row, ("占流通市值比例",)),
            "restricted_type": value_from(row, ("限售股类型",)),
            "source_name": "东方财富",
            "source_level": 2,
        }
        event_date = str(event.get("event_date") or "")[:10]
        if start and event_date < start:
            continue
        if end and event_date > end:
            continue
        normalized.append(event)
    result["records"] = sort_and_limit(normalized, "event_date", max_items)
    result["returned"] = len(result["records"])
    result["stock_code"] = code
    return result
