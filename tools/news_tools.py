import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from services.research_source_runner import run_akshare_provider
from tools.research_common import (
    normalize_date,
    normalize_stock_code,
    sort_and_limit,
    value_from,
)


def fetch_stock_news(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_items: int = 30,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    code = normalize_stock_code(stock_code)
    start = normalize_date(start_date, "start_date")
    end = normalize_date(end_date, "end_date")
    if start and end and start > end:
        raise ValueError("start_date不能晚于end_date")
    result = run_akshare_provider(
        "stock_news_em",
        {"symbol": code},
        timeout_seconds=timeout_seconds,
        max_records=100,
    )
    normalized = []
    seen = set()
    for row in result.get("records", []):
        published = value_from(row, ("发布时间",))
        published_date = str(published or "")[:10]
        if start and published_date < start:
            continue
        if end and published_date > end:
            continue
        url = value_from(row, ("新闻链接",))
        title = value_from(row, ("新闻标题",))
        dedupe_key = url or (title, published_date)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append({
            "stock_code": code,
            "title": title,
            "summary": value_from(row, ("新闻内容",)),
            "published_at": published,
            "source_name": value_from(row, ("文章来源",)) or "东方财富聚合",
            "source_level": 3,
            "source_url": url,
        })
    result["records"] = sort_and_limit(normalized, "published_at", max_items)
    result["returned"] = len(result["records"])
    result["stock_code"] = code
    return result


def search_news_tavily(
    query: str,
    max_items: int = 5,
    timeout_seconds: int = 15,
) -> Dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"status": "unavailable", "records": [], "error": "未配置TAVILY_API_KEY"}
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_items,
                "include_answer": False,
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        records = [{
            "title": item.get("title"),
            "summary": item.get("content"),
            "published_at": item.get("published_date"),
            "source_name": item.get("url", "").split("/")[2] if item.get("url") else None,
            "source_level": 3,
            "source_url": item.get("url"),
            "relevance_score": item.get("score"),
        } for item in payload.get("results", [])]
        return {
            "status": "completed",
            "provider": "tavily",
            "records": records,
            "returned": len(records),
            "collected_at": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "provider": "tavily",
            "records": [],
            "returned": 0,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
