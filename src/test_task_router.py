import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from workflow.task_router import classify_task, extract_stock_code


def main():
    cases = [
        ("筛选10只短线候选股票", "screen", False, None),
        ("查看000001的量化表现", "stock_query", False, "000001"),
        ("查询000001为什么得分高", "stock_query", True, "000001"),
        ("筛选候选股票并解释入选原因", "screen", True, None),
        ("", "screen", False, None),
    ]

    for query, task_type, explain, code in cases:
        result = classify_task(query)
        assert result["task_type"] == task_type, result
        assert result["explain"] is explain, result
        assert result["stock_code"] == code, result

    assert extract_stock_code("股票000001和20260820") == "000001"
    assert extract_stock_code("没有代码") is None

    print("通过：全市场筛选识别")
    print("通过：指定个股识别")
    print("通过：解释意图识别")
    print("通过：股票代码提取")
    print("通过：空请求使用筛选默认路径")


if __name__ == "__main__":
    main()
