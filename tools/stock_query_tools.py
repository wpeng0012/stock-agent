from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from tools.scoring_tools import calculate_scores


BASE_DIR = Path(__file__).resolve().parents[1]
FACTOR_FILE = BASE_DIR / "data" / "stock_factor_daily.csv"

REQUIRED_FIELDS = [
    "date", "code", "name", "close", "amount_ratio_1d",
    "turnover_ma5", "MA10", "MA20",
]

TECHNICAL_OUTPUT_FIELDS = [
    "amount_ratio_5d", "turnover_ratio_30d", "MA5", "MA10", "MA20",
    "ma_alignment", "ma5_ma10_cross", "ma20_slope_5d", "distance_ma20",
    "return_1d", "return_5d", "return_20d", "macd_dif", "macd_dea",
    "macd_hist", "macd_cross", "rsi6", "kdj_k", "kdj_d", "kdj_j",
    "kdj_cross", "atr14", "atr14_pct", "drawdown_20d", "drawdown_60d",
    "relative_strength_5d", "relative_strength_20d",
]


def _json_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    return float(value)


def resolve_stock(
    stock: str,
    factor_file: Path = FACTOR_FILE,
) -> Dict[str, Any]:
    """按代码或名称匹配股票，不让模型自行猜测代码。"""
    text = (stock or "").strip()
    if not text:
        return {"status": "invalid", "message": "请提供股票代码或名称"}

    df = pd.read_csv(factor_file, usecols=["code", "name"], dtype={"code": str})
    df["code"] = df["code"].str.zfill(6)
    basic = df.drop_duplicates("code").copy()

    if text.isdigit() and len(text) <= 6:
        matches = basic.loc[basic["code"] == text.zfill(6)]
    else:
        normalized = text.replace(" ", "")
        names = basic["name"].fillna("").astype(str).str.replace(" ", "", regex=False)
        matches = basic.loc[names.str.contains(normalized, regex=False, na=False)]

    if matches.empty:
        return {"status": "not_found", "query": text, "matches": []}
    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "query": text,
            "matches": matches[["code", "name"]].to_dict("records"),
        }

    row = matches.iloc[0]
    return {
        "status": "matched",
        "query": text,
        "code": str(row["code"]).zfill(6),
        "name": row["name"],
    }


def query_stock(
    stock: str,
    as_of: Optional[str] = None,
    factor_file: Path = FACTOR_FILE,
) -> Dict[str, Any]:
    """查询单只股票的最新可用因子和V1评分。"""
    resolved = resolve_stock(stock, factor_file)
    if resolved["status"] != "matched":
        return resolved

    df = pd.read_csv(factor_file, dtype={"code": str})
    df["code"] = df["code"].str.zfill(6)
    df = df.loc[df["code"] == resolved["code"]].copy()

    if as_of is not None:
        df = df.loc[df["date"] <= str(as_of)]
    if df.empty:
        return {
            "status": "no_data",
            "code": resolved["code"],
            "name": resolved["name"],
            "requested_as_of": as_of,
            "stocks": [],
        }

    data_as_of = str(df["date"].max())
    latest = df.loc[df["date"] == data_as_of].copy()
    missing = [field for field in REQUIRED_FIELDS if field not in latest.columns]
    if missing:
        return {"status": "invalid_data", "missing_fields": missing}

    scored = calculate_scores(latest)
    row = scored.iloc[0]
    normalized_name = str(row["name"]).upper().replace(" ", "")
    is_st = "ST" in normalized_name
    factor_missing = [
        field for field in [
            "close", "amount_ratio_1d", "turnover_ma5", "MA10", "MA20",
        ] if pd.isna(row[field])
    ]

    return {
        "status": "completed",
        "code": resolved["code"],
        "name": resolved["name"],
        "requested_as_of": as_of,
        "data_as_of": data_as_of,
        "screen_eligible": not is_st and not factor_missing,
        "exclusion_reasons": (["ST股票"] if is_st else [])
        + (["因子不完整"] if factor_missing else []),
        "score": None if factor_missing else int(row["score"]),
        "score_breakdown": None if factor_missing else {
            "amount": int(row["score_amount"]),
            "turnover": int(row["score_turnover"]),
            "trend": int(row["score_trend"]),
        },
        "factors": {
            "close": float(row["close"]),
            "amount_ratio_1d": float(row["amount_ratio_1d"]),
            "turnover_ma5": float(row["turnover_ma5"]),
            "MA10": None if pd.isna(row["MA10"]) else float(row["MA10"]),
            "MA20": None if pd.isna(row["MA20"]) else float(row["MA20"]),
            **{
                field: _json_value(row[field])
                for field in TECHNICAL_OUTPUT_FIELDS
                if field in row.index
            },
        },
    }
