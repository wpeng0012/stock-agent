import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.research_collection_service import collect_research_sources


def main():
    parser = argparse.ArgumentParser(description="按需检查个股研究数据源")
    parser.add_argument("stock_code")
    parser.add_argument("--stock-name")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument(
        "--scopes",
        nargs="+",
        default=["announcements", "events", "investor_qa", "news"],
    )
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    result = collect_research_sources(
        stock_code=args.stock_code,
        stock_name=args.stock_name,
        start_date=args.start_date,
        end_date=args.end_date,
        scopes=args.scopes,
        use_cache=not args.no_cache,
    )
    summary = {
        "status": result["status"],
        "stock_code": result["stock_code"],
        "start_date": result["start_date"],
        "end_date": result["end_date"],
        "cache_hit": result["cache_hit"],
        "sources": {
            name: {
                "status": source.get("status"),
                "returned": source.get("returned", len(source.get("records", []))),
                "error": source.get("error"),
            }
            for name, source in result["sources"].items()
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
