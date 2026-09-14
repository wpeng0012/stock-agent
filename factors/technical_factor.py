import numpy as np
import pandas as pd


def _group_transform(df, column, function):
    return df.groupby("code")[column].transform(function)


def calculate_technical_factor(df):
    """计算涨跌幅、MACD、RSI、KDJ、ATR、回撤和相对强弱。"""
    result = df.sort_values(["code", "date"]).copy()
    grouped = result.groupby("code", group_keys=False)

    for window in (1, 5, 20):
        result[f"return_{window}d"] = grouped["close"].pct_change(window)

    result["macd_ema12"] = _group_transform(
        result, "close", lambda x: x.ewm(span=12, adjust=False).mean()
    )
    result["macd_ema26"] = _group_transform(
        result, "close", lambda x: x.ewm(span=26, adjust=False).mean()
    )
    result["macd_dif"] = result["macd_ema12"] - result["macd_ema26"]
    result["macd_dea"] = _group_transform(
        result, "macd_dif", lambda x: x.ewm(span=9, adjust=False).mean()
    )
    result["macd_hist"] = 2 * (result["macd_dif"] - result["macd_dea"])
    previous_dif = result.groupby("code")["macd_dif"].shift(1)
    previous_dea = result.groupby("code")["macd_dea"].shift(1)
    result["macd_cross"] = "none"
    result.loc[
        (result["macd_dif"] > result["macd_dea"])
        & (previous_dif <= previous_dea),
        "macd_cross",
    ] = "golden"
    result.loc[
        (result["macd_dif"] < result["macd_dea"])
        & (previous_dif >= previous_dea),
        "macd_cross",
    ] = "dead"

    change = grouped["close"].diff()
    gain = change.clip(lower=0)
    loss = -change.clip(upper=0)
    avg_gain = gain.groupby(result["code"]).transform(
        lambda x: x.ewm(alpha=1 / 6, adjust=False, min_periods=6).mean()
    )
    avg_loss = loss.groupby(result["code"]).transform(
        lambda x: x.ewm(alpha=1 / 6, adjust=False, min_periods=6).mean()
    )
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result["rsi6"] = 100 - 100 / (1 + rs)
    result.loc[(avg_loss == 0) & (avg_gain > 0), "rsi6"] = 100.0
    result.loc[(avg_loss == 0) & (avg_gain == 0), "rsi6"] = 50.0

    low9 = _group_transform(result, "low", lambda x: x.rolling(9).min())
    high9 = _group_transform(result, "high", lambda x: x.rolling(9).max())
    price_range = (high9 - low9).replace(0, np.nan)
    result["kdj_rsv"] = ((result["close"] - low9) / price_range * 100).fillna(50.0)
    result["kdj_k"] = _group_transform(
        result, "kdj_rsv", lambda x: x.ewm(alpha=1 / 3, adjust=False).mean()
    )
    result["kdj_d"] = _group_transform(
        result, "kdj_k", lambda x: x.ewm(alpha=1 / 3, adjust=False).mean()
    )
    result["kdj_j"] = 3 * result["kdj_k"] - 2 * result["kdj_d"]
    previous_k = result.groupby("code")["kdj_k"].shift(1)
    previous_d = result.groupby("code")["kdj_d"].shift(1)
    result["kdj_cross"] = "none"
    result.loc[
        (result["kdj_k"] > result["kdj_d"]) & (previous_k <= previous_d),
        "kdj_cross",
    ] = "golden"
    result.loc[
        (result["kdj_k"] < result["kdj_d"]) & (previous_k >= previous_d),
        "kdj_cross",
    ] = "dead"

    previous_close = grouped["close"].shift(1)
    true_range = pd.concat(
        [
            result["high"] - result["low"],
            (result["high"] - previous_close).abs(),
            (result["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result["atr14"] = true_range.groupby(result["code"]).transform(
        lambda x: x.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    )
    result["atr14_pct"] = result["atr14"] / result["close"]

    for window in (20, 60):
        rolling_high = _group_transform(
            result, "close", lambda x, w=window: x.rolling(w).max()
        )
        result[f"drawdown_{window}d"] = result["close"] / rolling_high - 1

    # 当前行情文件没有指数序列，使用全市场当日收益中位数作为稳定基准。
    for window in (5, 20):
        market_median = result.groupby("date")[f"return_{window}d"].transform("median")
        result[f"relative_strength_{window}d"] = (
            result[f"return_{window}d"] - market_median
        )

    return result
