from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from main import run_pipeline
from services.run_store import create_run_id, load_run, save_run
from tools.stock_query_tools import query_stock
from tools.explanation_tools import explain_stock_score
from datetime import date
from services.event_research_service import run_event_research

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"]
)


class ResearchRequest(BaseModel):
    query: str = Field(default="筛选短线候选股票")
    as_of: Optional[date] = None
    top_n: int = Field(default=10, ge=1, le=100)


class StockQueryRequest(BaseModel):
    stock: str = Field(min_length=1)
    as_of: Optional[date] = None
    explain: bool = False


class EventResearchRequest(BaseModel):
    stock: str = Field(min_length=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    use_model: bool = True


@router.post("/research")
def research_stocks(request: ResearchRequest):
    return run_pipeline(
        query=request.query,
        as_of=str(request.as_of) if request.as_of else None,
        top_n=request.top_n
    )


@router.post("/query")
def query_single_stock(request: StockQueryRequest):
    run_id = create_run_id()
    result = query_stock(
        stock=request.stock,
        as_of=str(request.as_of) if request.as_of else None,
    )
    result["run_id"] = run_id
    result["task_type"] = "stock_query"
    result["explain_requested"] = request.explain
    if request.explain and result.get("status") == "completed":
        result["explanation"] = explain_stock_score(result)
    save_run(run_id=run_id, result=result)
    return result


@router.post("/event-research")
def research_stock_events(request: EventResearchRequest):
    run_id = create_run_id()
    try:
        result = run_event_research(
            stock_code=request.stock,
            start_date=str(request.start_date) if request.start_date else None,
            end_date=str(request.end_date) if request.end_date else None,
            use_model=request.use_model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["run_id"] = run_id
    save_run(run_id=run_id, result=result)
    return result

@router.get("/run")
def run_stock_agent():
    return run_pipeline(
        query="筛选短线候选股票",
        top_n=10
    )

@router.get("/runs/{run_id}")
def get_run(run_id: str):
    try:
        return load_run(run_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="run not found"
        )
