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


    return df