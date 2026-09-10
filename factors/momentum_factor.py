import pandas as pd


def calculate_momentum_factor(df):


    df = df.sort_values(
        [
            "code",
            "date"
        ]
    )


    # 5日涨幅

    df["return_5d"] = (

        df
        .groupby("code")["close"]
        .pct_change(5)

    )


    return df