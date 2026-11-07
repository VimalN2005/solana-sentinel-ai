import json
import os
import base64
from typing import Dict, Any, Optional, List
import httpx
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.message import Message
from solders.transaction import Transaction
from solders.hash import Hash
import base58

DEVNET_URL = "https://api.devnet.solana.com"
WALLET_FILE = os.path.join(os.path.dirname(__file__), "wallet.json")
TX_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "tx_history.json")

class SolanaClient:
    def __init__(self, rpc_url: str = DEVNET_URL):
        self.rpc_url = rpc_url
        self.keypair = self._load_or_create_wallet()
        self.spending_limit_per_tx = 0.5   # SOL
        self.daily_spending_limit = 2.0    # SOL
        self.spent_today = 0.0
        self.cached_balance = 0.0

    def _load_or_create_wallet(self) -> Keypair:
        if os.path.exists(WALLET_FILE):
            try:
                with open(WALLET_FILE, "r") as f:
                    data = json.load(f)
                    secret = bytes(data["secret_key"])
                    return Keypair.from_bytes(secret)
            except Exception as e:
                print(f"Error loading wallet: {e}")
        
        kp = Keypair()
        secret_list = list(bytes(kp))
        with open(WALLET_FILE, "w") as f:
            json.dump({
                "public_key": str(kp.pubkey()),
                "secret_key": secret_list
            }, f, indent=2)
        return kp

    @property
    def public_key_str(self) -> str:
        return str(self.keypair.pubkey())

    def _rpc_call(self, method: str, params: list, timeout: float = 4.0) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(self.rpc_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    def get_balance(self, address_str: Optional[str] = None) -> float:
        target_addr = address_str if address_str else self.public_key_str
        try:
            res = self._rpc_call("getBalance", [target_addr], timeout=3.0)
            lamports = res.get("result", {}).get("value", 0)
            bal = round(lamports / 1_000_000_000.0, 4)
            if not address_str:
                self.cached_balance = bal
            return bal
        except Exception as e:
            print(f"Warning fetching live balance, using cached {self.cached_balance} SOL: {e}")
            return self.cached_balance

    def request_airdrop(self, sol_amount: float = 1.0) -> Dict[str, Any]:
        lamports = int(sol_amount * 1_000_000_000)
        try:
            res = self._rpc_call("requestAirdrop", [self.public_key_str, lamports])
            if "error" in res:
                return {
                    "success": False,
                    "error": res["error"].get("message", "Devnet airdrop rate limit reached"),
                    "message": "Devnet faucet is currently rate-limited. You can also fund directly via https://faucet.solana.com"
                }
            signature = res.get("result")
            return {
                "success": True,
                "signature": signature,
                "amount": sol_amount,
                "message": f"Airdropped {sol_amount} SOL to your wallet on Devnet!",
                "explorer_url": f"https://explorer.solana.com/tx/{signature}?cluster=devnet"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to connect to Solana Devnet RPC"
            }

    def simulate_and_audit(self, recipient_str: str, sol_amount: float) -> Dict[str, Any]:
        """
        AI Pre-sign Security Guard:
        Analyzes policy constraints, valid addresses, balance sufficiency, and simulated RPC execution.
        """
        risk_flags = []
        risk_score = 0

        # 1. Format check
        try:
            recipient_pubkey = Pubkey.from_string(recipient_str)
        except Exception:
            return {
                "safe": False,
                "risk_score": 100,
                "risk_level": "CRITICAL",
                "risk_flags": ["Invalid base58 recipient address format."],
                "details": "Address does not conform to 32-byte Ed25519 Solana public key."
            }

        # 2. Self-transfer check
        if recipient_str == self.public_key_str:
            risk_flags.append("Recipient is the same as the sender treasury address.")
            risk_score += 10

        # 3. Policy: Single-tx spending limit
        if sol_amount > self.spending_limit_per_tx:
            risk_flags.append(f"Transfer of {sol_amount} SOL exceeds single-tx limit of {self.spending_limit_per_tx} SOL.")
            risk_score += 45

        # 4. Policy: Daily budget limit
        if (self.spent_today + sol_amount) > self.daily_spending_limit:
            risk_flags.append(f"Transfer pushes daily spend ({self.spent_today + sol_amount} SOL) past limit ({self.daily_spending_limit} SOL).")
            risk_score += 40

        # 5. Balance check
        current_bal = self.get_balance()
        if sol_amount > current_bal:
            risk_flags.append(f"Insufficient funds: Wallet has {current_bal} SOL, but requested {sol_amount} SOL.")
            risk_score += 55

        # 6. Simulate Transaction on Devnet
        sim_data = {"status": "ok"}
        try:
            lamports = int(sol_amount * 1_000_000_000)
            ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )

            # Get latest blockhash
            bh_res = self._rpc_call("getLatestBlockhash", [])
            blockhash_str = bh_res["result"]["value"]["blockhash"]
            recent_blockhash = Hash.from_string(blockhash_str)

            msg = Message.new_with_blockhash([ix], self.keypair.pubkey(), recent_blockhash)
            tx = Transaction.new_unsigned(msg)
            tx.sign([self.keypair], recent_blockhash)

            wire_tx = base64.b64encode(bytes(tx)).decode("utf-8")

            # Call RPC simulateTransaction
            sim_res = self._rpc_call("simulateTransaction", [wire_tx, {"encoding": "base64"}])
            val = sim_res.get("result", {}).get("value", {})
            err = val.get("err")
            if err:
                risk_flags.append(f"On-chain simulation returned an error: {err}")
                risk_score += 35
                sim_data["error"] = err
            sim_data["units_consumed"] = val.get("unitsConsumed")
            sim_data["logs"] = val.get("logs", [])
        except Exception as e:
            sim_data["exception"] = str(e)
            if sol_amount <= current_bal:
                risk_flags.append(f"Simulation warning: {str(e)[:100]}")
                risk_score += 15

        risk_score = min(100, risk_score)
        if risk_score == 0:
            risk_level = "VERIFIED_SAFE"
        elif risk_score <= 30:
            risk_level = "LOW_RISK"
        elif risk_score <= 65:
            risk_level = "ELEVATED_RISK"
        else:
            risk_level = "CRITICAL_BLOCKED"

        return {
            "safe": risk_score < 70,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_flags": risk_flags,
            "recipient": recipient_str,
            "amount_sol": sol_amount,
            "simulation": sim_data
        }

    def execute_transfer(self, recipient_str: str, sol_amount: float) -> Dict[str, Any]:
        audit = self.simulate_and_audit(recipient_str, sol_amount)
        if not audit["safe"]:
            return {
                "success": False,
                "error": "Transaction rejected by Solana Sentinel AI Guard: High risk score detected.",
                "audit": audit
            }

        try:
            recipient_pubkey = Pubkey.from_string(recipient_str)
            lamports = int(sol_amount * 1_000_000_000)

            ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )

            bh_res = self._rpc_call("getLatestBlockhash", [])
            blockhash_str = bh_res["result"]["value"]["blockhash"]
            recent_blockhash = Hash.from_string(blockhash_str)

            msg = Message.new_with_blockhash([ix], self.keypair.pubkey(), recent_blockhash)
            tx = Transaction.new_unsigned(msg)
            tx.sign([self.keypair], recent_blockhash)

            wire_tx = base64.b64encode(bytes(tx)).decode("utf-8")
            send_res = self._rpc_call("sendTransaction", [wire_tx, {"encoding": "base64"}])

            if "error" in send_res:
                return {
                    "success": False,
                    "error": send_res["error"].get("message", "RPC send error"),
                    "audit": audit
                }

            signature = send_res.get("result")
            self.spent_today += sol_amount

            # Record in history
            tx_record = {
                "signature": signature,
                "recipient": recipient_str,
                "amount_sol": sol_amount,
                "risk_score": audit["risk_score"],
                "risk_level": audit["risk_level"],
                "explorer_url": f"https://explorer.solana.com/tx/{signature}?cluster=devnet"
            }
            self._save_tx_history(tx_record)

            return {
                "success": True,
                "signature": signature,
                "amount_sol": sol_amount,
                "recipient": recipient_str,
                "explorer_url": f"https://explorer.solana.com/tx/{signature}?cluster=devnet",
                "audit": audit
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "audit": audit
            }

    def _save_tx_history(self, tx_record: Dict[str, Any]):
        history = self.get_tx_history()
        history.insert(0, tx_record)
        with open(TX_HISTORY_FILE, "w") as f:
            json.dump(history[:50], f, indent=2)

    def get_tx_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(TX_HISTORY_FILE):
            try:
                with open(TX_HISTORY_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
