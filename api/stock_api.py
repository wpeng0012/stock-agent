from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from main import run_pipeline
from services.run_store import load_run
from datetime import date

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"]
)


class ResearchRequest(BaseModel):
    query: str = Field(default="筛选短线候选股票")
    as_of: Optional[date] = None
    top_n: int = Field(default=10, ge=1, le=100)


@router.post("/research")
def research_stocks(request: ResearchRequest):
    return run_pipeline(
        query=request.query,
        as_of=str(request.as_of) if request.as_of else None,
        top_n=request.top_n
    )

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
