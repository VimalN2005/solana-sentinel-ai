import re
from typing import Dict, Any, Optional
from solana_client import SolanaClient

class SolanaSentinelAgent:
    def __init__(self, client: SolanaClient):
        self.client = client

    def process_message(self, user_msg: str) -> Dict[str, Any]:
        """
        Parses natural language requests and maps them to intelligent actions:
        - Check balance / treasury
        - Request airdrop
        - Audit transaction / simulate transfer
        - Set spending limits
        - General Solana help & advice
        """
        msg = user_msg.strip()
        lower_msg = msg.lower()

        # 1. Check Balance / Address
        if any(w in lower_msg for w in ["balance", "funds", "how much", "kitna balance", "sol", "address", "wallet"]):
            if "airdrop" not in lower_msg and "send" not in lower_msg and "transfer" not in lower_msg:
                bal = self.client.get_balance()
                return {
                    "type": "BALANCE_INFO",
                    "reply": f"**Solana Sentinel Treasury Status**\n\n- **Public Address:** `{self.client.public_key_str}`\n- **Devnet Balance:** **{bal} SOL**\n- **Single-Tx Limit:** `{self.client.spending_limit_per_tx} SOL`\n- **Daily Budget Limit:** `{self.client.daily_spending_limit} SOL` (Spent today: `{self.client.spent_today} SOL`)",
                    "data": {
                        "balance": bal,
                        "address": self.client.public_key_str,
                        "single_limit": self.client.spending_limit_per_tx,
                        "daily_limit": self.client.daily_spending_limit
                    }
                }

        # 2. Request Airdrop
        if any(w in lower_msg for w in ["airdrop", "faucet", "fund", "free sol", "paise do"]):
            # Extract amount if mentioned
            match = re.search(r"(\d+(\.\d+)?)", msg)
            amount = float(match.group(1)) if match else 1.0
            amount = min(amount, 2.0)  # Cap at 2 SOL per request
            result = self.client.request_airdrop(amount)
            if result.get("success"):
                return {
                    "type": "AIRDROP_SUCCESS",
                    "reply": f"**Devnet Airdrop Successful!**\n\nAdded **{amount} SOL** to `{self.client.public_key_str}`.\n\n[View on Solana Explorer]({result.get('explorer_url')})",
                    "data": result
                }
            else:
                return {
                    "type": "AIRDROP_RATE_LIMITED",
                    "reply": f"⚠️ **Devnet Faucet Notice:**\n\n{result.get('message')}\n\nYou can also paste your address (`{self.client.public_key_str}`) directly at [Solana Devnet Faucet](https://faucet.solana.com) to claim free test SOL immediately.",
                    "data": result
                }

        # 3. Transfer / Send Sol
        if any(w in lower_msg for w in ["send", "transfer", "pay", "bhejo"]):
            # Extract SOL amount
            amount_match = re.search(r"(\d+(\.\d+)?)\s*(sol)?", lower_msg)
            amount = float(amount_match.group(1)) if amount_match else None

            # Extract base58 recipient address (typical length 32-44 chars base58)
            addr_match = re.search(r"[1-9A-HJ-NP-Za-km-z]{32,44}", msg)
            recipient = addr_match.group(0) if addr_match else None

            if not recipient or not amount:
                return {
                    "type": "TRANSFER_PROMPT",
                    "reply": "To initiate an autonomous transfer or simulation, please specify the recipient Solana address and amount.\n\n**Example:** `Send 0.05 SOL to 8CbTYuPR4heSuwRaobezX7s8L2cPEMRweS4x48Tjxhdc`"
                }

            # Run pre-sign simulation and security audit first!
            audit = self.client.simulate_and_audit(recipient, amount)

            flags_formatted = "\n".join([f"- ⚠️ {f}" for f in audit["risk_flags"]]) if audit["risk_flags"] else "- ✅ Zero anomalies detected. Standard SystemProgram transfer."

            reply = f"""### 🛡️ Solana Sentinel Pre-Sign Audit Report

- **Recipient:** `{recipient}`
- **Amount:** **{amount} SOL**
- **Security Assessment:** **{audit['risk_level']}** (Risk Score: **{audit['risk_score']}/100**)
- **Safety Policy:** {'✅ APPROVED' if audit['safe'] else '🛑 BLOCKED / CAUTION'}

**Security Findings:**
{flags_formatted}
"""
            if audit["safe"]:
                reply += "\n*Click **Execute Transfer** to broadcast this transaction to Solana Devnet.*"
            else:
                reply += "\n*This transaction was flagged due to policy restrictions or insufficient balance.*"

            return {
                "type": "AUDIT_RESULT",
                "reply": reply,
                "data": {
                    "audit": audit,
                    "recipient": recipient,
                    "amount": amount
                }
            }

        # 4. Set Limits
        if "limit" in lower_msg:
            match = re.search(r"(\d+(\.\d+)?)", msg)
            if match:
                new_limit = float(match.group(1))
                if "daily" in lower_msg:
                    self.client.daily_spending_limit = new_limit
                    scope = "Daily budget"
                else:
                    self.client.spending_limit_per_tx = new_limit
                    scope = "Single-transaction limit"
                return {
                    "type": "LIMIT_UPDATED",
                    "reply": f"✅ **Spending Policy Updated!**\n\n{scope} is now set to **{new_limit} SOL**."
                }

        # 5. Default Help / Assistant
        return {
            "type": "GENERAL_HELP",
            "reply": f"""I am **Solana Sentinel**, an autonomous AI agent with on-chain execution and pre-sign security auditing on Solana Devnet.

**Here is what I can do for you:**
1. 📊 **Treasury & Balance:** *"What is my balance?"*
2. 🚰 **Devnet Faucet:** *"Request 1 SOL from airdrop"*
3. 🛡️ **Simulate & Audit Transfer:** *"Send 0.05 SOL to [Solana Address]"*
4. ⚙️ **Enforce Spending Limits:** *"Set single limit to 0.2 SOL"* or *"Set daily budget to 1.5 SOL"*

**Your Active Treasury Address:** `{self.client.public_key_str}`"""
        }
