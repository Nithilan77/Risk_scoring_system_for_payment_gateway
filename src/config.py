"""
config.py
---------
All tunable parameters for the risk scoring engine live here.

WHY THIS FILE EXISTS:
The weights below are reasoned judgments, NOT values derived from data.
This dataset has no fraud label, so there is nothing to statistically
optimise the weights against. Instead, each weight reflects how much
genuine signal the Phase 1 audit found in that feature. Keeping them in
one file makes that judgment transparent and adjustable — change a number
here and the whole engine respects it, with no logic changes.

HONEST NOTE ON WHAT THE SCORE MEANS:
The final score is an ANOMALY / DEVIATION score (0-100): how unusual is a
transaction versus the account's own normal behaviour. It is NOT a fraud
probability. We have no fraud labels, so no probability claim is possible.
"""

# ---------------------------------------------------------------------------
# FEATURE WEIGHTS  (must sum to 1.0)
# ---------------------------------------------------------------------------
# Reasoning for each weight comes directly from the Phase 1 data audit:
#
#   amount    0.25  - strongest, most reliable per-account signal. Amounts
#                     vary widely and z-scores against a per-account baseline
#                     are meaningful.
#   location  0.20  - genuinely viable here (median 5 locations/account). A
#                     transaction from a never-seen location is a strong
#                     behavioural anomaly.
#   balance   0.15  - real, varying per account. Spending a large fraction of
#                     available balance is a sensible risk signal.
#   merchant  0.15  - viable (median 5 merchants/account). New merchant for an
#                     account is a moderate anomaly.
#   velocity  0.12  - derived from TransactionDate (NOT PreviousTransactionDate,
#                     which the audit proved is an artifact). Bursts of activity
#                     are a classic risk signal.
#   max_amt   0.08  - exceeding an account's historical max is informative but
#                     overlaps with the amount z-score, so weighted lower.
#   login     0.03  - LoginAttempts is mostly 1 but ~5% of rows show 2-5
#                     attempts; small but real account-takeover signal.
#   hour      0.02  - WEAK on this dataset. Every transaction falls in a
#                     16:00-18:00 window, so time-of-day carries almost no
#                     signal. Included because it was requested, weighted
#                     near-zero because the data does not support it.
#
WEIGHTS = {
    "amount":   0.25,
    "location": 0.20,
    "balance":  0.15,
    "merchant": 0.15,
    "velocity": 0.12,
    "max_amt":  0.08,
    "login":    0.03,
    "hour":     0.02,
}

# ---------------------------------------------------------------------------
# DECISION THRESHOLDS
# ---------------------------------------------------------------------------
# Map the 0-100 anomaly score to an action. These cutoffs are conventional
# (see industry explainers using ~ <30 allow, 30-70 review, >70 block) and
# are adjustable. They describe how UNUSUAL a transaction is, not fraud odds.
THRESHOLDS = {
    "allow":     30,   # score < 30  -> allow (looks normal for this account)
    "review":    70,   # 30 <= score < 70 -> flag for step-up / review
    # score >= 70 -> block / manual review
}

# ---------------------------------------------------------------------------
# SCORER PARAMETERS
# ---------------------------------------------------------------------------
# z-score at which the amount sub-score saturates to 100.
# z=4 means "4 std deviations above the account mean" is treated as maximal.
AMOUNT_Z_SATURATION = 4.0

# Fraction of available balance spent at which the balance sub-score saturates.
# 0.9 means "spending >=90% of (balance+amount)" is maximal risk.
BALANCE_DRAIN_SATURATION = 0.90

# Velocity: how many times the account's average daily count must be exceeded
# for the velocity sub-score to saturate. 3.0 = "3x your normal daily volume".
VELOCITY_SATURATION_MULT = 3.0

# Accounts with fewer than this many transactions are flagged low-confidence.
LOW_HISTORY_THRESHOLD = 5

# Sub-score (0-100) assigned for a brand-new location / merchant.
NEW_LOCATION_SCORE = 100
NEW_MERCHANT_SCORE = 100

# Hours considered "normal" for this dataset (audit showed 16-18 only).
# A transaction outside this window scores higher on the (low-weight) hour
# feature. Kept honest: this barely matters given weight 0.02.
NORMAL_HOURS = {16, 17, 18}
