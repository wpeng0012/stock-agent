import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import workflow.graph as graph_module


class FakeResponse:
    content = '{"as_of": null}'


class FakeModel:
    def invoke(self, prompt):
        return FakeResponse()


def main():
    original_model = graph_module.get_deepseek_model
    original_research = graph_module.run_event_research
    original_quant = graph_module.run_quant_agent
    graph_module.get_deepseek_model = lambda: FakeModel()
    graph_module.run_event_research = lambda **kwargs: {
        "status": "completed",
        "task_type": "event_research",
        "stock_code": kwargs["stock_code"],
    }
    graph_module.run_quant_agent = lambda **kwargs: {
        "status": "completed",
        "stocks": [
            {"code": "000001", "name": "平安银行"},
            {"code": "600519", "name": "贵州茅台"},
            {"code": "300750", "name": "宁德时代"},
        ],
    }

    try:
        screen_state = graph_module.plan_node({
            "query": "筛选10只短线候选股票",
            "top_n": 10,
        })
        assert screen_state["task_type"] == "screen"
        assert screen_state["explain"] is False

        stock_state = graph_module.plan_node({
            "query": "查看000001的量化表现并解释原因",
            "top_n": 10,
        })
        assert stock_state["task_type"] == "stock_query"
        assert stock_state["stock_code"] == "000001"
        assert stock_state["explain"] is True

        query_result = graph_module.quant_node(stock_state)
        assert query_result["status"] == "completed"
        assert query_result["result"]["code"] == "000001"

        research_state = graph_module.plan_node({
            "query": "研究000001最近的新闻公告",
            "top_n": 3,
        })
        assert research_state["task_type"] == "event_research"
        research_result = graph_module.quant_node(research_state)
        assert research_result["result"]["task_type"] == "event_research"

        screen_research_state = graph_module.plan_node({
            "query": "筛选3只股票并研究新闻公告",
            "top_n": 3,
        })
        screen_research_result = graph_module.quant_node(screen_research_state)
        assert screen_research_result["result"]["task_type"] == "screen_research"
        assert len(screen_research_result["result"]["research_results"]) == 3
        assert query_result["result"]["task_type"] == "stock_query"

        print("通过：筛选请求进入screen任务")
        print("通过：个股请求提取代码")
        print("通过：个股请求进入真实查询路径")
    finally:
        graph_module.get_deepseek_model = original_model
        graph_module.run_event_research = original_research
        graph_module.run_quant_agent = original_quant


if __name__ == "__main__":
    main()
