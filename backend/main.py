import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from solana_client import SolanaClient
from agent import SolanaSentinelAgent

app = FastAPI(title="Solana Sentinel AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = SolanaClient()
agent = SolanaSentinelAgent(client)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

class ChatRequest(BaseModel):
    message: str

class TransferRequest(BaseModel):
    recipient: str
    amount_sol: float

class SimulateRequest(BaseModel):
    recipient: str
    amount_sol: float

class LimitRequest(BaseModel):
    single_tx_limit: Optional[float] = None
    daily_limit: Optional[float] = None

@app.get("/api/wallet")
def get_wallet():
    return {
        "public_key": client.public_key_str,
        "balance_sol": client.get_balance(),
        "single_limit": client.spending_limit_per_tx,
        "daily_limit": client.daily_spending_limit,
        "spent_today": client.spent_today,
        "network": "Solana Devnet",
        "rpc_url": client.rpc_url
    }

@app.post("/api/faucet")
def request_faucet(amount: float = 1.0):
    res = client.request_airdrop(amount)
    return res

@app.post("/api/chat")
def chat(req: ChatRequest):
    return agent.process_message(req.message)

@app.post("/api/simulate")
def simulate(req: SimulateRequest):
    return client.simulate_and_audit(req.recipient, req.amount_sol)

@app.post("/api/transfer")
def execute_transfer(req: TransferRequest):
    res = client.execute_transfer(req.recipient, req.amount_sol)
    return res

@app.get("/api/transactions")
def get_transactions():
    return client.get_tx_history()

@app.post("/api/limits")
def update_limits(req: LimitRequest):
    if req.single_tx_limit is not None:
        client.spending_limit_per_tx = req.single_tx_limit
    if req.daily_limit is not None:
        client.daily_spending_limit = req.daily_limit
    return {
        "single_limit": client.spending_limit_per_tx,
        "daily_limit": client.daily_spending_limit
    }

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Solana Sentinel AI API is running. Frontend index.html not found."}

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
