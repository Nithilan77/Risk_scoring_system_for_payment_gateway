"""
main.py
-------
FastAPI service for the risk scoring engine.

Exposes the engine over HTTP so a transaction can be scored in real time.
The response is an ANOMALY / DEVIATION score (0-100) with a full explainable
breakdown — never a fraud probability (no fraud labels exist in this data).

Endpoints:
    GET  /health              - service health + profile count
    GET  /account/{id}        - view an account's behavioural baseline
    POST /score               - score a single transaction
    POST /score/batch         - score multiple transactions

Run:
    uvicorn main:app --reload --port 9000
Docs:
    http://localhost:9000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path
import logging

from engine import RiskEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# profiles produced by Phase 2 (account_profiles.json)
PROFILES_PATH = Path(__file__).resolve().parent.parent / "data" / "account_profiles.json"

app = FastAPI(
    title="Payment Gateway Risk Scoring API",
    description=(
        "Scores how UNUSUAL a transaction is versus an account's own normal "
        "behaviour. Returns a 0-100 anomaly score with an explainable "
        "breakdown. This is a behavioural risk/anomaly score, NOT a fraud "
        "probability — the underlying data has no fraud labels."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# load engine once at startup
engine = RiskEngine(str(PROFILES_PATH))
logger.info(f"Risk engine loaded with {len(engine.profiles)} account profiles")


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class Transaction(BaseModel):
    account_id: str = Field(..., example="AC00202")
    amount: float = Field(..., ge=0, example=1947.84)
    location: str = Field(..., example="Reykjavik")
    merchant: str = Field(..., example="M015")
    current_balance: float = Field(..., ge=0, example=3980.30)
    txns_today: int = Field(1, ge=1, example=1)
    login_attempts: int = Field(1, ge=1, example=1)
    hour: int = Field(..., ge=0, le=23, example=16)


class BatchRequest(BaseModel):
    transactions: List[Transaction] = Field(..., min_length=1, max_length=1000)


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "profiles_loaded": len(engine.profiles),
        "score_type": "anomaly/deviation (0-100), not fraud probability",
        "version": "1.0.0",
    }


@app.get("/account/{account_id}", tags=["Account"])
def get_account(account_id: str):
    """View the behavioural baseline the engine scores against for an account."""
    profile = engine.profiles.get(account_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No profile for account {account_id}")
    # summarise so the response is readable (don't dump full merchant list)
    return {
        "account_id": account_id,
        "txn_count": profile["txn_count"],
        "low_confidence": profile["txn_count"] < 5,
        "amt_mean": profile["amt_mean"],
        "amt_std": profile["amt_std"],
        "amt_max": profile["amt_max"],
        "avg_balance": profile["avg_balance"],
        "avg_daily_txns": profile["avg_daily_txns"],
        "customer_age": profile["customer_age"],
        "known_locations": profile["known_locations"],
        "n_known_merchants": len(profile["known_merchants"]),
        "typical_hours": profile["typical_hours"],
    }


@app.post("/score", tags=["Scoring"])
def score(txn: Transaction):
    """Score a single transaction. Returns 0-100 anomaly score + breakdown."""
    result = engine.score_transaction(txn.model_dump())
    if result.get("risk_score") is None and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    logger.info(
        f"Scored {txn.account_id}: {result['risk_score']} ({result['decision']})"
    )
    return result


@app.post("/score/batch", tags=["Scoring"])
def score_batch(req: BatchRequest):
    """Score multiple transactions in one call."""
    results = []
    for t in req.transactions:
        r = engine.score_transaction(t.model_dump())
        results.append(r)

    scored = [r for r in results if r.get("risk_score") is not None]
    summary = {
        "total": len(results),
        "scored": len(scored),
        "allow": sum(1 for r in scored if r["decision"] == "ALLOW"),
        "review": sum(1 for r in scored if r["decision"] == "REVIEW"),
        "block": sum(1 for r in scored if r["decision"] == "BLOCK"),
    }
    return {"summary": summary, "results": results}
