import pandas as pd


def calculate_trend_factor(df):


    """
    计算均线趋势

    MA5
    MA10
    MA20

    """


    df = df.sort_values(
        [
            "code",
            "date"
        ]
    )


    for window in [5,10,20]:


        df[f"MA{window}"] = (

            df
            .groupby("code")["close"]
            .transform(
                lambda x:
                x.rolling(window)
                .mean()
            )

        )

    grouped = df.groupby("code", group_keys=False)
    previous_ma5 = grouped["MA5"].shift(1)
    previous_ma10 = grouped["MA10"].shift(1)

    df["ma_alignment"] = "mixed"
    df.loc[
        (df["MA5"] > df["MA10"]) & (df["MA10"] > df["MA20"]),
        "ma_alignment",
    ] = "bullish"
    df.loc[
        (df["MA5"] < df["MA10"]) & (df["MA10"] < df["MA20"]),
        "ma_alignment",
    ] = "bearish"

    df["ma5_ma10_cross"] = "none"
    df.loc[
        (df["MA5"] > df["MA10"])
        & (previous_ma5 <= previous_ma10),
        "ma5_ma10_cross",
    ] = "golden"
    df.loc[
        (df["MA5"] < df["MA10"])
        & (previous_ma5 >= previous_ma10),
        "ma5_ma10_cross",
    ] = "dead"

    df["ma20_slope_5d"] = grouped["MA20"].pct_change(5)
    df["distance_ma20"] = df["close"] / df["MA20"] - 1


    return df
