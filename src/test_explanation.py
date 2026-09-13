import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.explanation_tools import explain_stock_score


def main():
    result = explain_stock_score({
        "price": 12.0,
        "score": 100,
        "score_breakdown": {"amount": 40, "turnover": 30, "trend": 30},
        "factors": {
            "amount_ratio_1d": 1.8,
            "turnover_ma5": 0.05,
            "MA10": 11.0,
            "MA20": 11.5,
        },
    })
    assert result["rule_version"] == "v1"
    assert len(result["reasons"]) == 3
    assert all("分" in reason for reason in result["reasons"])
    print("通过：解释包含三项评分依据")
    print("通过：解释使用结构化因子和分项得分")


if __name__ == "__main__":
    main()
