import pandas as pd


def calculate_liquidity_factor(df):


    df = df.sort_values(
        [
            "code",
            "date"
        ]
    )


    df["turnover_ma5"] = (

        df
        .groupby("code")["turnover"]
        .transform(
            lambda x:
            x.rolling(5).mean()
        )

    )

    # 用此前30个交易日作为个股自身换手基准，排除当天。
    df["turnover_ma30_prev"] = (
        df.groupby("code")["turnover"]
        .transform(lambda x: x.shift(1).rolling(30).mean())
    )
    df["turnover_ratio_30d"] = (
        df["turnover"] / df["turnover_ma30_prev"]
    )


    return df
