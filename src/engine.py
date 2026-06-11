"""
engine.py
---------
The scoring engine. Loads account profiles, scores a transaction across all
features, aggregates them with the configured weights, and returns a final
0-100 ANOMALY score plus a full, human-readable breakdown.

KEY HONESTY PROPERTIES:
  - The score is an anomaly/deviation score, never a "fraud probability".
  - Every transaction's score comes with a per-feature breakdown so any
    decision is fully explainable (which features drove the score and why).
  - Accounts with thin history are flagged low_confidence in the output; the
    score is still computed but explicitly marked as not authoritative.
"""

import json
from config import WEIGHTS, THRESHOLDS, LOW_HISTORY_THRESHOLD
import scorers


class RiskEngine:
    def __init__(self, profiles_path):
        with open(profiles_path, "r") as f:
            self.profiles = json.load(f)

    # -- helpers ------------------------------------------------------------
    def _decision(self, score):
        if score < THRESHOLDS["allow"]:
            return "ALLOW"
        if score < THRESHOLDS["review"]:
            return "REVIEW"
        return "BLOCK"

    def _reason(self, feature, sub, txn, profile):
        """Short human-readable explanation per feature."""
        if feature == "amount":
            return (f"amount {txn['amount']:.2f} vs account avg "
                    f"{profile['amt_mean']:.2f} (std {profile['amt_std']:.2f})")
        if feature == "max_amt":
            return f"amount {txn['amount']:.2f} vs historical max {profile['amt_max']:.2f}"
        if feature == "location":
            known = "known" if sub == 0 else "NEW for this account"
            return f"location '{txn['location']}' is {known}"
        if feature == "merchant":
            known = "known" if sub == 0 else "NEW for this account"
            return f"merchant '{txn['merchant']}' is {known}"
        if feature == "balance":
            avail = txn["current_balance"] + txn["amount"]
            frac = txn["amount"] / avail if avail > 0 else 0
            return f"spends {frac*100:.0f}% of available funds"
        if feature == "velocity":
            return (f"{txn['txns_today']} txns today vs avg "
                    f"{profile.get('avg_daily_txns',1):.1f}/day")
        if feature == "login":
            return f"{txn.get('login_attempts',1)} login attempt(s)"
        if feature == "hour":
            return f"hour {txn['hour']} (dataset is 16-18h; low signal)"
        return ""

    # -- main API -----------------------------------------------------------
    def score_transaction(self, txn):
        """
        txn is a dict with keys:
          account_id, amount, location, merchant, current_balance,
          txns_today, login_attempts, hour
        Returns a dict: final score, decision, confidence, breakdown.
        """
        acct = txn["account_id"]
        profile = self.profiles.get(acct)

        if profile is None:
            return {
                "account_id": acct,
                "error": "No profile for this account. Cannot score against a "
                         "baseline that does not exist.",
                "risk_score": None,
            }

        # compute each sub-score
        subs = {
            "amount":   scorers.score_amount(txn["amount"], profile),
            "max_amt":  scorers.score_max_amount(txn["amount"], profile),
            "location": scorers.score_location(txn["location"], profile),
            "merchant": scorers.score_merchant(txn["merchant"], profile),
            "balance":  scorers.score_balance(txn["amount"], txn["current_balance"], profile),
            "velocity": scorers.score_velocity(txn["txns_today"], profile),
            "login":    scorers.score_login(txn.get("login_attempts", 1)),
            "hour":     scorers.score_hour(txn["hour"]),
        }

        # weighted aggregate
        final = sum(subs[f] * WEIGHTS[f] for f in WEIGHTS)
        final = round(final, 2)

        # build explainable breakdown, sorted by contribution
        breakdown = []
        for f in WEIGHTS:
            contribution = round(subs[f] * WEIGHTS[f], 2)
            breakdown.append({
                "feature": f,
                "sub_score": round(subs[f], 2),
                "weight": WEIGHTS[f],
                "contribution": contribution,
                "reason": self._reason(f, subs[f], txn, profile),
            })
        breakdown.sort(key=lambda x: x["contribution"], reverse=True)

        low_conf = profile["txn_count"] < LOW_HISTORY_THRESHOLD

        return {
            "account_id": acct,
            "risk_score": final,            # 0-100 ANOMALY score, not fraud prob
            "decision": self._decision(final),
            "confidence": "low" if low_conf else "normal",
            "baseline_txns": profile["txn_count"],
            "confidence_note": (
                f"Baseline built from only {profile['txn_count']} transactions; "
                "treat score as indicative, not authoritative."
                if low_conf else
                f"Baseline built from {profile['txn_count']} transactions."
            ),
            "breakdown": breakdown,
        }
