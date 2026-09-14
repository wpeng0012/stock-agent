import re
from typing import Any, Dict, List


EVENT_RULES = [
    ("share_unlock", ("解禁", "上市流通"), "high"),
    ("private_placement", ("定向增发", "向特定对象发行", "增发", "配股", "再融资"), "high"),
    ("repurchase", ("回购",), "high"),
    ("holder_change", ("减持", "增持", "持股变动"), "high"),
    ("earnings", ("业绩预告", "业绩快报", "年度报告", "半年度报告", "季度报告"), "high"),
    ("dividend", ("利润分配", "权益分派", "分红", "送转"), "medium"),
    ("major_contract", ("重大合同", "中标", "订单", "战略合作"), "high"),
    ("merger", ("重组", "收购", "重大资产", "控制权变更"), "high"),
    ("equity_incentive", ("股权激励", "限制性股票", "员工持股"), "medium"),
    ("legal_risk", ("诉讼", "仲裁", "立案", "处罚", "问询函", "监管函"), "high"),
    ("guarantee_pledge", ("担保", "质押"), "medium"),
    ("risk_notice", ("风险提示", "异常波动", "退市风险", "停牌", "复牌"), "high"),
    ("management", ("董事", "监事", "高级管理人员", "任职资格"), "low"),
]


def classify_event(title: str) -> Dict[str, str]:
    normalized = re.sub(r"\s+", "", str(title or ""))
    for event_type, keywords, importance in EVENT_RULES:
        if any(keyword in normalized for keyword in keywords):
            return {"event_type": event_type, "importance": importance}
    return {"event_type": "other", "importance": "low"}


def build_evidence(sources: Dict[str, Any], max_items: int = 30) -> List[Dict[str, Any]]:
    candidates = []
    for source_key, source in sources.items():
        for record in source.get("records", []):
            title = record.get("title") or record.get("question") or record.get("event_type") or "未命名事件"
            classified = classify_event(title)
            if source_key == "investor_qa":
                classified = {"event_type": "investor_qa", "importance": "medium"}
            if record.get("event_type") == "share_unlock":
                classified = {"event_type": "share_unlock", "importance": "high"}
            candidates.append({
                "source_key": source_key,
                "source_level": record.get("source_level", 3),
                "source_name": record.get("source_name"),
                "source_url": record.get("source_url"),
                "published_at": record.get("published_at") or record.get("event_date") or record.get("answer_time"),
                "title": title,
                "summary": record.get("summary") or record.get("answer") or "",
                "event_type": classified["event_type"],
                "importance": classified["importance"],
                "facts": {
                    key: value for key, value in record.items()
                    if key not in {"summary", "answer", "question", "title", "source_url"}
                    and value is not None
                },
            })

    importance_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda item: str(item.get("published_at") or ""), reverse=True)
    candidates.sort(key=lambda item: (
        importance_order[item["importance"]], item["source_level"]
    ))
    result = []
    seen = set()
    for item in candidates:
        identity = item.get("source_url") or (
            re.sub(r"\W+", "", item["title"]), str(item.get("published_at") or "")[:10]
        )
        if identity in seen:
            continue
        seen.add(identity)
        item["evidence_id"] = f"E{len(result) + 1:03d}"
        result.append(item)
        if len(result) >= max_items:
            break
    return result
