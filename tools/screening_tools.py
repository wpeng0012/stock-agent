from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FACTOR_FILE = BASE_DIR / "data" / "stock_factor_daily.csv"


def screen_candidates(
    as_of: Optional[str] = None,
    top_n: int = 10,
    factor_file: Path = FACTOR_FILE,
) -> Dict[str, Any]:
    """Run the existing V1 deterministic screening rules.

    The function is intentionally independent of LangChain/LangGraph so it can
    be used from the CLI, API, or an agent node.
    """
    if top_n < 1 or top_n > 100:
        raise ValueError("top_n must be between 1 and 100")

    df = pd.read_csv(factor_file, dtype={"code": str})
    required = {"date", "code", "name", "close", "amount_ratio_1d", "turnover_ma5", "MA10", "MA20"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError("missing factor columns: " + ", ".join(missing))

    data_as_of = str(df["date"].max())
    if as_of is not None:
        available = df[df["date"] <= str(as_of)]
        if available.empty:
            return {"status": "no_data", "data_as_of": None, "stocks": [], "missing_fields": ["date"]}
        data_as_of = str(available["date"].max())
        df = available

    latest = df[df["date"] == data_as_of].copy()
    latest = latest[~latest["name"].fillna("").str.contains("ST", na=False)]
    latest = latest.dropna(
        subset=[
            "close",
            "amount_ratio_1d",
            "turnover_ma5",
            "MA10",
            "MA20"
        ]
    )
    latest["score_amount"] = 0
    latest.loc[latest["amount_ratio_1d"] > 1.5, "score_amount"] = 40
    latest.loc[latest["amount_ratio_1d"].between(1.2, 1.5, inclusive="both"), "score_amount"] = 30
    latest.loc[latest["amount_ratio_1d"].between(1.0, 1.2, inclusive="left"), "score_amount"] = 20
    latest["score_turnover"] = 0
    latest.loc[latest["turnover_ma5"].between(0.03, 0.10, inclusive="both"), "score_turnover"] = 30
    latest.loc[latest["turnover_ma5"].between(0.10, 0.15, inclusive="right"), "score_turnover"] = 20
    latest["score_trend"] = 0
    latest.loc[latest["close"] > latest["MA20"], "score_trend"] = 30
    latest.loc[(latest["close"] > latest["MA10"]) & (latest["close"] <= latest["MA20"]), "score_trend"] = 20
    latest["score"] = latest[["score_amount", "score_turnover", "score_trend"]].sum(axis=1)
    latest = latest.sort_values(["score", "code"], ascending=[False, True]).head(top_n)

    stocks: List[Dict[str, Any]] = []

    for _, row in latest.iterrows():
        stocks.append({
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
        })
    return {"status": "completed", "data_as_of": data_as_of, "stocks": stocks, "missing_fields": []}
