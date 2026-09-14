import pandas as pd


def calculate_volume_factor(df):

    """
    计算资金活跃度指标

    amount_ratio_1d:
    今日成交额 / 昨日成交额
    """


    # 按股票和日期排序
    df = df.sort_values(
        [
            "code",
            "date"
        ]
    )


    # 昨日成交额

    df["prev_amount"] = (
        df
        .groupby("code")["amount"]
        .shift(1)
    )


    # 成交额变化

    df["amount_ratio_1d"] = (
        df["amount"]
        /
        df["prev_amount"]
    )

    # 今日成交额与此前5个交易日平均成交额比较；基准排除当天。
    df["amount_ma5_prev"] = (
        df.groupby("code")["amount"]
        .transform(lambda x: x.shift(1).rolling(5).mean())
    )
    df["amount_ratio_5d"] = df["amount"] / df["amount_ma5_prev"]


    return df
