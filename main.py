import json

from services.run_store import create_run_id, save_run
from workflow.graph import stock_graph


def run_pipeline(
    query="筛选短线候选股票",
    as_of=None,
    top_n=10
):
    run_id = create_run_id()

    result = stock_graph.invoke({
        "query": query,
        "as_of": as_of,
        "top_n": top_n
    })

    result["run_id"] = run_id

    save_run(
        run_id=run_id,
        result=result
    )

    return result


if __name__ == "__main__":
    result = run_pipeline()

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )