# 🛡️ Solana Sentinel AI
> **Autonomous Agentic Treasury & Pre-Sign Security Guard on Solana**  
> *Submitted to MLH Solana Hackathon (Nov 6–8, 2026) | Target Tracks: Top 3 Overall & AI Track*

---

## 🌟 The Problem
1. **Machine-to-Machine Payments**: Autonomous AI agents need to pay for tools, APIs, and data feeds, but legacy payment rails cannot support sub-cent, 400ms micropayments.
2. **Blind-Signing Exploits & Drainers**: Users and automated systems executing Solana transactions frequently suffer from malicious drainers and unintended token approvals due to opaque transaction payloads.

## 🚀 The Solution: Solana Sentinel AI
**Solana Sentinel AI** bridges autonomous agentic workflows with Solana's high-speed, low-cost settlement layer.

- 🤖 **Autonomous Natural Language Interface**: Interacts with users and other agents to manage treasury balances, request testnet faucets, and execute transfers with spending limits.
- 🛡️ **Pre-Sign Security Simulation**: Before any transaction is signed or broadcast, Sentinel simulates execution on Solana Devnet via RPC, decodes instruction logs, checks policy constraints, and computes a comprehensive **Risk Score (0 to 100)**.
- ⚙️ **Enforced Spending Policies**: Granular limits on single-transaction amounts and daily budget caps to prevent catastrophic treasury depletion.
- 🔗 **Direct Devnet Verification**: Real-time broadcast and instant verification on Solana Explorer.

---

## 🏗️ Architecture
```
┌────────────────────────────────────────────────────────┐
│               Modern Cyber UI (Glassmorphic)          │
│   (Agent Chat, Treasury Meter, Pre-Sign Audit, History) │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Backend Server                │
│    (/api/chat, /api/wallet, /api/simulate, /api/transfer)│
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
┌─────────────▼───────────────┐ ┌─────────▼──────────────┐
│    SolanaSentinelAgent      │ │      SolanaClient      │
│  - Intent & Policy Parser   │ │  - Solders Ed25519     │
│  - Spending Limit Enforcer  │ │  - Devnet JSON-RPC     │
│  - Risk Classification      │ │  - simulateTransaction │
└─────────────────────────────┘ └─────────┬──────────────┘
                                          │
                               ┌──────────▼──────────────┐
                               │   Solana Devnet RPC     │
                               │ (api.devnet.solana.com) │
                               └─────────────────────────┘
```

---

## 🛠️ Quick Start

### 1. Requirements
- Python 3.10+
- `fastapi`, `uvicorn`, `solders`, `solana`, `httpx`, `pydantic`

### 2. Start the Server
```bash
cd backend
python main.py
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## 🏆 MLH Challenges & Hackathon Fit
- **AI Track**: Real AI-driven security auditing, natural language parsing, and autonomous machine micropayments.
- **Top 3 Overall**: Built specifically for Solana's native advantages (sub-second finality, micro-gas fees, composability).
- **Best Beginner Hack**: High polish, complete full-stack delivery, zero external blockchain dependencies required.
