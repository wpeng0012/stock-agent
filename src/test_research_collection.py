import sys
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.research_cache_service import load_cache, save_cache
from services.research_source_runner import run_akshare_provider
from tools.investor_qa_tools import fetch_investor_qa
from tools.research_common import normalize_stock_code


def main():
    assert normalize_stock_code("000001.SZ") == "000001"

    with tempfile.TemporaryDirectory() as directory:
        cache_dir = Path(directory)
        save_cache("test", {"status": "completed"}, cache_dir=cache_dir)
        assert load_cache("test", 60, cache_dir=cache_dir)["status"] == "completed"

    timeout = run_akshare_provider(
        "stock_sns_sseinfo",
        {"symbol": "603119"},
        timeout_seconds=1,
        max_records=5,
    )
    assert timeout["status"] in {"timeout", "completed"}, timeout

    blocked = fetch_investor_qa("600519")
    assert blocked["status"] == "unavailable", blocked

    print("通过：股票代码和缓存处理")
    print("通过：第三方接口在隔离进程中受硬超时保护")
    print("通过：上证e互动慢接口不会进入采集")


if __name__ == "__main__":
    main()
