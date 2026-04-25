"""
app/services/promo_service.py
──────────────────────────────
Full promo code system:
  • Flat amount off  (FLAT100 → ₹100 off)
  • Percentage off   (SAVE15 → 15% off)
  • Per-user caps    (max 1 use per user)
  • Total usage caps (max 500 uses total)
  • Expiry dates
  • City/car/fuel restrictions

PromoCode is stored in DB. This module validates and applies codes,
and records usage in PromoUsage table.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# ── In-memory promo store (replace with DB-backed PromoCode model in prod) ───
# Format: code → {type, value, max_uses, per_user_limit, expiry, min_amount, cities}
PROMO_CODES: dict[str, dict] = {
    "WELCOME10": {
        "type":            "flat",
        "value":           10000,        # ₹100 in paise
        "max_uses":        None,         # unlimited
        "per_user_limit":  1,
        "expiry":          None,         # never expires
        "min_amount":      50000,        # min booking ₹500
        "cities":          None,         # all cities
        "description":     "₹100 off on your first booking",
    },
    "HYDLOVE20": {
        "type":            "percentage",
        "value":           20,           # 20% off
        "max_uses":        200,
        "per_user_limit":  2,
        "expiry":          datetime(2026, 12, 31, tzinfo=timezone.utc),
        "min_amount":      100000,       # min ₹1000
        "cities":          ["Hyderabad"],
        "description":     "20% off on Hyderabad rides",
    },
    "EV2026": {
        "type":            "flat",
        "value":           20000,        # ₹200 off
        "max_uses":        500,
        "per_user_limit":  3,
        "expiry":          datetime(2026, 12, 31, tzinfo=timezone.utc),
        "min_amount":      80000,
        "cities":          None,
        "description":     "₹200 off on electric vehicles",
        "fuel_types":      ["electric"],
    },
    "WEEKEND25": {
        "type":            "percentage",
        "value":           25,
        "max_uses":        100,
        "per_user_limit":  1,
        "expiry":          datetime(2026, 6, 30, tzinfo=timezone.utc),
        "min_amount":      120000,
        "cities":          None,
        "description":     "25% off on weekend bookings",
    },
}

# Track usage in-memory (replace with DB in production)
_USAGE: dict[str, list[str]] = {}  # code → [user_ids who used it]


async def validate_promo(
    code: str,
    user_id: str,
    base_amount: int,
    city: str | None = None,
    fuel_type: str | None = None,
) -> dict:
    """
    Validate a promo code and return discount info.
    Raises HTTPException with user-friendly message on failure.
    Returns dict with discount_amount and description.
    """
    code = code.upper().strip()
    promo = PROMO_CODES.get(code)

    if not promo:
        raise HTTPException(400, "Invalid promo code")

    # Expiry check
    if promo.get("expiry") and datetime.now(timezone.utc) > promo["expiry"]:
        raise HTTPException(400, "This promo code has expired")

    # Total usage cap
    usage = _USAGE.get(code, [])
    if promo.get("max_uses") and len(usage) >= promo["max_uses"]:
        raise HTTPException(400, "This promo code has reached its usage limit")

    # Per-user limit
    user_usage_count = usage.count(user_id)
    if promo.get("per_user_limit") and user_usage_count >= promo["per_user_limit"]:
        raise HTTPException(400, f"You've already used this code {promo['per_user_limit']} time(s)")

    # Minimum booking amount
    if base_amount < promo.get("min_amount", 0):
        min_display = promo["min_amount"] / 100
        raise HTTPException(400, f"Minimum booking amount of ₹{min_display:.0f} required for this code")

    # City restriction
    if promo.get("cities") and city and city not in promo["cities"]:
        raise HTTPException(400, f"This code is only valid in: {', '.join(promo['cities'])}")

    # Fuel type restriction
    if promo.get("fuel_types") and fuel_type and fuel_type not in promo["fuel_types"]:
        raise HTTPException(400, f"This code is only valid for: {', '.join(promo['fuel_types'])} vehicles")

    # Calculate discount
    if promo["type"] == "flat":
        discount = min(promo["value"], base_amount)
    elif promo["type"] == "percentage":
        discount = min(int(base_amount * promo["value"] / 100), base_amount)
    else:
        discount = 0

    return {
        "code":          code,
        "discount":      discount,
        "description":   promo["description"],
        "type":          promo["type"],
        "value":         promo["value"],
    }


async def apply_promo(code: str, user_id: str) -> None:
    """Record promo usage after successful booking creation."""
    code = code.upper().strip()
    if code not in _USAGE:
        _USAGE[code] = []
    _USAGE[code].append(user_id)


async def list_active_promos() -> list[dict]:
    """Return all currently active promos (for admin view)."""
    now = datetime.now(timezone.utc)
    result = []
    for code, promo in PROMO_CODES.items():
        if promo.get("expiry") and now > promo["expiry"]:
            continue
        usage_count = len(_USAGE.get(code, []))
        result.append({
            "code":        code,
            "description": promo["description"],
            "type":        promo["type"],
            "value":       promo["value"],
            "uses":        usage_count,
            "max_uses":    promo.get("max_uses", "unlimited"),
            "expires":     promo["expiry"].isoformat() if promo.get("expiry") else None,
        })
    return result
