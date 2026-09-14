import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.event_classification_service import build_evidence, classify_event
from services.event_research_service import _load_skill_instructions
from workflow.task_router import classify_task


def main():
    assert "Do not use Tushare" in _load_skill_instructions()
    assert classify_event("关于限售股份上市流通的公告")["event_type"] == "share_unlock"
    assert classify_event("关于向特定对象发行股票的预案")["event_type"] == "private_placement"
    assert classify_event("关于回购股份进展的公告")["event_type"] == "repurchase"
    assert classify_task("研究一下830799最近的公告")["stock_code"] == "830799"

    routed = classify_task("研究一下000001最近的新闻和公告")
    assert routed["task_type"] == "event_research", routed
    routed = classify_task("筛选3只股票并研究新闻公告")
    assert routed["task_type"] == "screen_research", routed

    evidence = build_evidence({
        "announcements": {"records": [{
            "title": "关于回购股份的公告",
            "published_at": "2026-09-01",
            "source_level": 1,
            "source_name": "巨潮资讯",
            "source_url": "https://example.com/a",
        }]},
        "news": {"records": [{
            "title": "关于回购股份的公告",
            "published_at": "2026-09-01",
            "source_level": 3,
            "source_name": "转载",
            "source_url": "https://example.com/a",
        }]},
    })
    assert len(evidence) == 1, evidence
    assert evidence[0]["evidence_id"] == "E001"

    print("通过：公告事件分类")
    print("通过：个股研究和筛选后研究路由")
    print("通过：重复证据合并和证据编号")


if __name__ == "__main__":
    main()
