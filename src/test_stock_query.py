import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.stock_query_tools import query_stock, resolve_stock


FACTOR_PREVIEW = BASE_DIR / "output" / "factor_update_preview.csv"


def main():
    matched = resolve_stock("000001", FACTOR_PREVIEW)
    assert matched["status"] == "matched", matched
    assert matched["code"] == "000001", matched

    result = query_stock("000001", factor_file=FACTOR_PREVIEW)
    assert result["status"] == "completed", result
    assert result["data_as_of"] == "2026-09-11", result
    assert result["score"] is not None, result
    assert result["screen_eligible"] is True, result

    st_result = query_stock("000010", factor_file=FACTOR_PREVIEW)
    assert st_result["status"] == "completed", st_result
    assert st_result["screen_eligible"] is False, st_result
    assert "ST股票" in st_result["exclusion_reasons"], st_result

    missing = query_stock("999999", factor_file=FACTOR_PREVIEW)
    assert missing["status"] == "not_found", missing

    no_data = query_stock(
        "000001",
        as_of="2020-01-01",
        factor_file=FACTOR_PREVIEW,
    )
    assert no_data["status"] == "no_data", no_data

    print("通过：代码匹配和个股查询")
    print("通过：返回实际数据日期和评分")
    print("通过：ST股票标记为不可选")
    print("通过：无匹配股票处理")
    print("通过：无历史数据日期处理")


if __name__ == "__main__":
    main()
