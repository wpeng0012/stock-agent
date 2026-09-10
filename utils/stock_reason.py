def generate_reason(row):

    reasons = []


    # 资金

    if row["amount_ratio_1d"] >= 3:
        reasons.append(
            "成交额明显放大"
        )

    elif row["amount_ratio_1d"] >= 1.5:
        reasons.append(
            "成交额温和放大"
        )


    # 换手

    if row["turnover_ma5"] >= 0.05:
        reasons.append(
            "近期换手活跃"
        )


    # 趋势

    if (
        row["MA5"]
        >
        row["MA10"]
        >
        row["MA20"]
    ):
        reasons.append(
            "均线多头排列"
        )

    elif row["close"] > row["MA20"]:
        reasons.append(
            "价格站上20日均线"
        )


    # 动量

    if row["return_5d"] >= 0.05:

        reasons.append(
            "短期上涨趋势明显"
        )


    return "；".join(reasons)