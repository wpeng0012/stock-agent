from typing import Any, Dict, List


def explain_stock_score(stock: Dict[str, Any]) -> Dict[str, Any]:
    """根据已计算的因子和分项得分生成可追溯的规则解释。"""
    factors = stock.get("factors", {})
    breakdown = stock.get("score_breakdown") or {}
    reasons: List[str] = []

    amount = factors.get("amount_ratio_1d")
    if amount is not None:
        if amount > 1.5:
            reasons.append(f"成交额为前一交易日的{amount:.2f}倍，获得{breakdown.get('amount', 0)}分")
        elif amount >= 1.2:
            reasons.append(f"成交额为前一交易日的{amount:.2f}倍，获得{breakdown.get('amount', 0)}分")
        elif amount >= 1.0:
            reasons.append(f"成交额较前一交易日增加{(amount - 1) * 100:.1f}%，获得{breakdown.get('amount', 0)}分")
        else:
            reasons.append(f"成交额为前一交易日的{amount:.2f}倍，该项获得{breakdown.get('amount', 0)}分")

    turnover = factors.get("turnover_ma5")
    if turnover is not None:
        reasons.append(f"5日平均换手率为{turnover:.2%}，该项获得{breakdown.get('turnover', 0)}分")

    close = stock.get("price", factors.get("close"))
    ma10 = factors.get("MA10")
    ma20 = factors.get("MA20")
    if close is not None and ma20 is not None and close > ma20:
        reasons.append(f"收盘价{close:.2f}高于MA20 {ma20:.2f}，趋势项获得{breakdown.get('trend', 0)}分")
    elif close is not None and ma10 is not None and ma20 is not None and close > ma10:
        reasons.append(f"收盘价{close:.2f}高于MA10 {ma10:.2f}但未高于MA20 {ma20:.2f}，趋势项获得{breakdown.get('trend', 0)}分")
    else:
        reasons.append(f"均线趋势项获得{breakdown.get('trend', 0)}分")

    return {
        "total_score": stock.get("score"),
        "reasons": reasons,
        "rule_version": "v1",
    }
