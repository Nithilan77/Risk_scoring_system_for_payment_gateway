"""
scorers.py
----------
One scoring function per feature. Each takes the current transaction and the
account's profile, and returns a sub-score in [0, 100] describing how UNUSUAL
the transaction is on that single dimension.

Design rules followed throughout:
  - Every function returns a float in [0, 100].
  - Higher = more unusual = higher risk.
  - Functions never raise on missing/edge data; they degrade to 0 (treat as
    "not unusual") rather than crash, and the engine handles confidence
    separately via the low_history flag.
  - No function knows about fraud labels. These measure deviation only.
"""

from config import (
    AMOUNT_Z_SATURATION,
    BALANCE_DRAIN_SATURATION,
    VELOCITY_SATURATION_MULT,
    NEW_LOCATION_SCORE,
    NEW_MERCHANT_SCORE,
    NORMAL_HOURS,
)


def _clamp(x):
    """Keep any value inside [0, 100]."""
    return float(max(0.0, min(100.0, x)))


def score_amount(amount, profile):
    """
    How far above the account's normal spend is this amount?
    Uses a one-sided z-score (only ABOVE the mean is risky; spending less
    than usual is not a risk). z is scaled so that AMOUNT_Z_SATURATION std
    devs maps to 100.
    """
    mean = profile["amt_mean"]
    std  = profile["amt_std"]          # already floored >= 1.0 in profile build
    if std <= 0:
        return 0.0
    z = (amount - mean) / std
    if z <= 0:
        return 0.0                     # at or below normal -> not unusual
    return _clamp((z / AMOUNT_Z_SATURATION) * 100)


def score_max_amount(amount, profile):
    """
    Does this transaction exceed the account's historical maximum?
    If yes, score scales with how far beyond the max it goes (capped).
    If within the historical max, 0.
    """
    amt_max = profile["amt_max"]
    if amt_max <= 0 or amount <= amt_max:
        return 0.0
    # how many % beyond the previous max; 100% beyond (2x) -> saturates
    over = (amount - amt_max) / amt_max
    return _clamp(over * 100)


def score_location(location, profile):
    """
    Has this account transacted from this location before?
    Known location -> 0 (normal). New location -> NEW_LOCATION_SCORE.
    This is binary by nature: either the account has used this city or not.
    """
    if location in profile["known_locations"]:
        return 0.0
    return float(NEW_LOCATION_SCORE)


def score_merchant(merchant, profile):
    """
    Has this account used this merchant before?
    Known merchant -> 0. New merchant -> NEW_MERCHANT_SCORE.
    """
    if merchant in profile["known_merchants"]:
        return 0.0
    return float(NEW_MERCHANT_SCORE)


def score_balance(amount, current_balance, profile):
    """
    What fraction of available funds does this transaction consume?
    available = current_balance + amount  (balance is post-transaction in the
    data, so pre-transaction funds ~= current_balance + amount).
    Spending a large fraction is riskier. Saturates at BALANCE_DRAIN_SATURATION.
    """
    available = current_balance + amount
    if available <= 0:
        return 0.0
    frac = amount / available
    return _clamp((frac / BALANCE_DRAIN_SATURATION) * 100)


def score_velocity(txns_today, profile):
    """
    Is the account transacting far more than its normal daily volume?
    txns_today is the count of this account's transactions on the day of the
    transaction being scored. Saturates at VELOCITY_SATURATION_MULT x average.
    """
    avg = profile.get("avg_daily_txns", 1.0)
    if avg <= 0:
        avg = 1.0
    ratio = txns_today / avg
    if ratio <= 1.0:
        return 0.0                     # at or below normal volume
    # ratio of VELOCITY_SATURATION_MULT -> 100
    excess = (ratio - 1.0) / (VELOCITY_SATURATION_MULT - 1.0)
    return _clamp(excess * 100)


def score_login(login_attempts):
    """
    Multiple login attempts before a transaction is a small account-takeover
    signal. 1 attempt -> 0. Each extra attempt adds 25, capping at 100.
    """
    if login_attempts <= 1:
        return 0.0
    return _clamp((login_attempts - 1) * 25)


def score_hour(hour):
    """
    Time-of-day. HONEST CAVEAT: on this dataset all transactions fall in
    16:00-18:00, so this carries almost no signal and is weighted ~0 in config.
    A transaction outside the normal window scores 100, else 0.
    """
    if hour in NORMAL_HOURS:
        return 0.0
    return 100.0
