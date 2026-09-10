from typing import Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.quant_agent import run_quant_agent
from datetime import datetime


class StockState(TypedDict, total=False):
    query: str
    as_of: str
    top_n: int
    status: str
    result: Dict[str, Any]


from runtime.model import get_deepseek_model


def plan_node(state: StockState) -> StockState:
    import json

    query = state.get("query", "")
    current_top_n = state.get("top_n", 10)
    current_as_of = state.get("as_of")

    prompt = f"""
你是A股量化筛选任务规划助手。

用户请求：
{query}

当前默认参数：
top_n={current_top_n}
as_of={current_as_of}

只输出JSON，不要输出其他文字：
{{
  "top_n": null,
  "as_of": null
}}

规则：
1. 1. top_n由程序传入，不能修改。
2. 只解析as_of日期。
3. 不要计算股票指标。
4. 不要输出股票名称或股票代码。
5. 如果用户明确给出日期，as_of使用YYYY-MM-DD格式。
6. 用户没有给出日期时，as_of保持null。
"""

    response = get_deepseek_model().invoke(prompt)
    content = response.content.strip()

    try:
        parsed = json.loads(content)

        top_n = current_top_n
        top_n = max(
            1,
            min(
                top_n,
                100
            )
        )

        as_of = parsed.get(
            "as_of",
            current_as_of
        )

        if as_of in ("null", "", None):
            as_of = current_as_of
        else:
            datetime.strptime(
                as_of,
                "%Y-%m-%d"
            )

            if as_of > datetime.now().strftime("%Y-%m-%d"):
                as_of = None


    except Exception:

        top_n = current_top_n

        as_of = current_as_of

    return {
        "top_n": top_n,
        "as_of": as_of,
        "status": "planned"
    }

def quant_node(state: StockState) -> StockState:
    result = run_quant_agent(
        as_of=state.get("as_of"),
        top_n=state.get("top_n", 10)
    )
    return {"result": result, "status": result["status"]}


def build_graph():
    graph = StateGraph(StockState)
    graph.add_node("plan", plan_node)
    graph.add_node("quant", quant_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "quant")
    graph.add_edge("quant", END)
    return graph.compile()


stock_graph = build_graph()
