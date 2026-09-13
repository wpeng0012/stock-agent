import pandas as pd


def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """根据现有 V1 规则计算分项得分和总分。"""
    result = df.copy()

    # 成交额变化：最高 40 分
    result["score_amount"] = 0
    result.loc[
        result["amount_ratio_1d"] > 1.5,
        "score_amount"
    ] = 40
    result.loc[
        result["amount_ratio_1d"].between(
            1.2, 1.5, inclusive="both"
        ),
        "score_amount"
    ] = 30
    result.loc[
        result["amount_ratio_1d"].between(
            1.0, 1.2, inclusive="left"
        ),
        "score_amount"
    ] = 20

    # 5 日平均换手率：最高 30 分
    result["score_turnover"] = 0
    result.loc[
        result["turnover_ma5"].between(
            0.03, 0.10, inclusive="both"
        ),
        "score_turnover"
    ] = 30
    result.loc[
        result["turnover_ma5"].between(
            0.10, 0.15, inclusive="right"
        ),
        "score_turnover"
    ] = 20

    # 均线趋势：最高 30 分
    result["score_trend"] = 0
    result.loc[
        result["close"] > result["MA20"],
        "score_trend"
    ] = 30
    result.loc[
        (result["close"] > result["MA10"])
        & (result["close"] <= result["MA20"]),
        "score_trend"
    ] = 20

    result["score"] = result[
        ["score_amount", "score_turnover", "score_trend"]
    ].sum(axis=1)

    return result