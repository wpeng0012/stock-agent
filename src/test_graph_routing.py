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
    graph_module.get_deepseek_model = lambda: FakeModel()

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
        assert query_result["result"]["task_type"] == "stock_query"

        print("通过：筛选请求进入screen任务")
        print("通过：个股请求提取代码")
        print("通过：个股请求进入真实查询路径")
    finally:
        graph_module.get_deepseek_model = original_model


if __name__ == "__main__":
    main()
