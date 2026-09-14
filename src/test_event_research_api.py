import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
import api.stock_api as stock_api
from api.api_main import app


def main():
    original = stock_api.run_event_research
    stock_api.run_event_research = lambda **kwargs: {
        "status": "completed",
        "task_type": "event_research",
        "stock_code": kwargs["stock_code"],
        "evidence": [{"evidence_id": "E001"}],
        "report": {"summary": "测试研究结果"},
    }
    try:
        response = TestClient(app).post("/stocks/event-research", json={
            "stock": "000001",
            "start_date": "2026-09-01",
            "end_date": "2026-09-14",
            "use_model": False,
        })
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["task_type"] == "event_research"
        assert payload["run_id"]
        assert (BASE_DIR / "output" / "runs" / f"{payload['run_id']}.json").exists()
        print("通过：事件研究API和run_id结果保存")
    finally:
        stock_api.run_event_research = original


if __name__ == "__main__":
    main()
