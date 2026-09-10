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


    return df