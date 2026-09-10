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


    return df