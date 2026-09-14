import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from services.research_cache_service import load_cache, save_cache
from tools.announcement_tools import fetch_announcements
from tools.event_tools import fetch_unlock_events
from tools.investor_qa_tools import fetch_investor_qa
from tools.news_tools import fetch_stock_news, search_news_tavily
from tools.research_common import normalize_date, normalize_stock_code


ALLOWED_SCOPES = {"announcements", "events", "investor_qa", "news"}


def collect_research_sources(
    stock_code: str,
    stock_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    scopes: Iterable[str] = ALLOWED_SCOPES,
    use_cache: bool = True,
    cache_ttl_seconds: int = 6 * 60 * 60,
) -> Dict[str, Any]:
    code = normalize_stock_code(stock_code)
    end = normalize_date(end_date, "end_date") or date.today().isoformat()
    start = normalize_date(start_date, "start_date") or (
        datetime.strptime(end, "%Y-%m-%d").date() - timedelta(days=7)
    ).isoformat()
    if start > end:
        raise ValueError("start_date不能晚于end_date")
    if (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days > 90:
        raise ValueError("单次研究时间范围不能超过90天")
    selected = list(dict.fromkeys(scopes))
    unknown = sorted(set(selected) - ALLOWED_SCOPES)
    if unknown:
        raise ValueError(f"不支持的研究范围：{unknown}")

    cache_key = json.dumps(
        {"schema": 2, "code": code, "name": stock_name, "start": start, "end": end, "scopes": selected},
        ensure_ascii=False,
        sort_keys=True,
    )
    if use_cache:
        cached = load_cache(cache_key, cache_ttl_seconds)
        if cached:
            cached["cache_hit"] = True
            return cached

    sources: Dict[str, Any] = {}
    if "announcements" in selected:
        sources["announcements"] = fetch_announcements(code, start, end)
    if "events" in selected:
        sources["events"] = fetch_unlock_events(code, start, end)
    if "investor_qa" in selected:
        sources["investor_qa"] = fetch_investor_qa(code)
    if "news" in selected:
        sources["stock_news"] = fetch_stock_news(code, start, end)
        query_name = f"{stock_name} {code}" if stock_name else code
        sources["web_news"] = search_news_tavily(
            f"{query_name} 公司新闻 公告 行业政策 {start} 至 {end}"
        )

    statuses = [item.get("status") for item in sources.values()]
    completed = sum(status == "completed" for status in statuses)
    status = "completed" if completed == len(statuses) else "partial" if completed else "failed"
    result = {
        "status": status,
        "stock_code": code,
        "stock_name": stock_name,
        "start_date": start,
        "end_date": end,
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "cache_hit": False,
        "sources": sources,
    }
    if use_cache:
        save_cache(cache_key, result)
    return result
