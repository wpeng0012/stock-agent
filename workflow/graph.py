from typing import Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.quant_agent import run_quant_agent
from datetime import datetime
from workflow.task_router import classify_task
from tools.stock_query_tools import query_stock
from tools.explanation_tools import explain_stock_score
from services.event_research_service import run_event_research


class StockState(TypedDict, total=False):
    query: str
    as_of: str
    top_n: int
    status: str
    result: Dict[str, Any]
    task_type: str
    task_name: str
    stock_code: str
    stock_name: str
    explain: bool


from runtime.model import get_deepseek_model


def plan_node(state: StockState) -> StockState:
    import json

    query = state.get("query", "")
    current_top_n = state.get("top_n", 10)
    current_as_of = state.get("as_of")
    task = classify_task(query)

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
        "task_type": task["task_type"],
        "task_name": task["task_name"],
        "stock_code": task["stock_code"],
        "stock_name": task["stock_name"],
        "explain": task["explain"],
        "top_n": top_n,
        "as_of": as_of,
        "status": "planned"
    }

def quant_node(state: StockState) -> StockState:
    if state.get("task_type") == "event_research":
        result = run_event_research(
            stock_code=state.get("stock_code") or "",
            stock_name=state.get("stock_name"),
            end_date=state.get("as_of"),
        )
        return {"result": result, "status": result["status"]}

    if state.get("task_type") == "screen_research":
        quant_result = run_quant_agent(
            as_of=state.get("as_of"),
            top_n=min(state.get("top_n", 3), 3),
        )
        if quant_result.get("status") != "completed":
            return {"result": quant_result, "status": quant_result["status"]}
        research_results = []
        for stock in quant_result.get("stocks", [])[:3]:
            research_results.append(run_event_research(
                stock_code=stock["code"],
                stock_name=stock.get("name"),
                end_date=state.get("as_of"),
            ))
        research_statuses = [item.get("status") for item in research_results]
        combined_status = (
            "completed"
            if research_statuses and all(status == "completed" for status in research_statuses)
            else "partial"
        )
        return {
            "result": {
                "status": combined_status,
                "task_type": "screen_research",
                "quant_result": quant_result,
                "research_results": research_results,
            },
            "status": combined_status,
        }

    if state.get("task_type") == "stock_query":
        result = query_stock(
            stock=state.get("stock_code") or state.get("stock_name") or "",
            as_of=state.get("as_of"),
        )
        result["task_type"] = "stock_query"
        if state.get("explain") and result.get("status") == "completed":
            result["explanation"] = explain_stock_score(result)
        return {"result": result, "status": result["status"]}

    result = run_quant_agent(
        as_of=state.get("as_of"),
        top_n=state.get("top_n", 10)
    )
    if state.get("explain") and result.get("status") == "completed":
        for stock in result.get("stocks", []):
            stock["explanation"] = explain_stock_score(stock)
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
