import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.event_research_service import run_event_research


def main():
    parser = argparse.ArgumentParser(description="运行单只A股新闻公告研究")
    parser.add_argument("stock_code")
    parser.add_argument("--stock-name")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--no-model", action="store_true")
    args = parser.parse_args()
    result = run_event_research(
        stock_code=args.stock_code,
        stock_name=args.stock_name,
        start_date=args.start_date,
        end_date=args.end_date,
        use_model=not args.no_model,
    )
    summary = {
        "status": result.get("status"),
        "task_type": result.get("task_type"),
        "stock_code": result.get("stock_code"),
        "stock_name": result.get("stock_name"),
        "start_date": result.get("start_date"),
        "end_date": result.get("end_date"),
        "cache_hit": result.get("cache_hit"),
        "analysis_status": result.get("analysis_status"),
        "evidence_count": len(result.get("evidence", [])),
        "event_types": sorted({
            item.get("event_type") for item in result.get("evidence", [])
            if item.get("event_type")
        }),
        "evidence_dates": sorted({
            str(item.get("published_at"))[:10] for item in result.get("evidence", [])
            if item.get("published_at")
        }),
        "pdf_documents": sum(
            bool(item.get("document_excerpt")) for item in result.get("evidence", [])
        ),
        "report": result.get("report"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
