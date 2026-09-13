from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from tools.scoring_tools import calculate_scores


BASE_DIR = Path(__file__).resolve().parents[1]
FACTOR_FILE = BASE_DIR / "data" / "stock_factor_daily.csv"


def screen_candidates(
    as_of: Optional[str] = None,
    top_n: int = 10,
    factor_file: Path = FACTOR_FILE,
) -> Dict[str, Any]:
    """读取因子数据，使用公共评分函数筛选候选股票。"""

    if top_n < 1 or top_n > 100:
        raise ValueError("top_n must be between 1 and 100")

    df = pd.read_csv(
        factor_file,
        dtype={"code": str}
    )

    required = {
        "date",
        "code",
        "name",
        "close",
        "amount_ratio_1d",
        "turnover_ma5",
        "MA10",
        "MA20",
    }

    missing = sorted(required.difference(df.columns))

    if missing:
        raise ValueError(
            "missing factor columns: " + ", ".join(missing)
        )

    data_as_of = str(df["date"].max())

    if as_of is not None:
        available = df[df["date"] <= str(as_of)]

        if available.empty:
            return {
                "status": "no_data",
                "data_as_of": None,
                "stocks": [],
                "missing_fields": ["date"],
            }

        data_as_of = str(available["date"].max())
        df = available

    # 取实际数据日期对应的股票
    latest = df[df["date"] == data_as_of].copy()

    # 排除名称中包含 ST 的股票
    normalized_names = (
        latest["name"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.replace(" ", "", regex=False)
    )
    latest = latest[~normalized_names.str.contains("ST", na=False)]

    # 排除评分所需因子缺失的股票
    latest = latest.dropna(
        subset=[
            "close",
            "amount_ratio_1d",
            "turnover_ma5",
            "MA10",
            "MA20",
        ]
    )

    # 调用公共评分函数
    latest = calculate_scores(latest)

    # 按总分降序排列，同分时按股票代码排列
    latest = latest.sort_values(
        ["score", "code"],
        ascending=[False, True]
    ).head(top_n)

    stocks: List[Dict[str, Any]] = []

    for _, row in latest.iterrows():
        stocks.append(
            {
                "code": str(row["code"]).zfill(6),
                "name": row["name"],
                "price": float(row["close"]),
                "data_as_of": data_as_of,
                "score": int(row["score"]),
                "score_breakdown": {
                    "amount": int(row["score_amount"]),
                    "turnover": int(row["score_turnover"]),
                    "trend": int(row["score_trend"]),
                },
                "factors": {
                    "amount_ratio_1d": float(row["amount_ratio_1d"]),
                    "turnover_ma5": float(row["turnover_ma5"]),
                    "MA10": float(row["MA10"]),
                    "MA20": float(row["MA20"]),
                },
            }
        )

    return {
        "status": "completed",
        "data_as_of": data_as_of,
        "stocks": stocks,
        "missing_fields": [],
    }
