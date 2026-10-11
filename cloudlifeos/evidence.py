"""Freshness projection, never a capability registry or authority grant."""
from datetime import datetime, timezone

FLAGS = ("connected", "authenticated", "admitted", "verified_working")


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def project(record, now=None):
    now = now or datetime.now(timezone.utc)
    result = dict(record)
    observed = timestamp(record.get("observed_at"))
    ttl = record.get("ttl_seconds")
    valid_ttl = isinstance(ttl, (int, float)) and not isinstance(ttl, bool) and 0 < ttl <= 86400
    age = (now - observed).total_seconds() if observed else None
    if not observed or not valid_ttl or age < -5:
        freshness = "unknown"
    elif age > ttl:
        freshness = "stale"
    else:
        freshness = "current"
    # An offline snapshot is never evidence of current runtime availability.
    effective = {
        name: record.get(name) if freshness == "current" and record.get("mode") == "live" else None
        for name in FLAGS
    }
    for name, value in effective.items():
        if value is not True and value is not False:
            effective[name] = None
    result.update(freshness=freshness, effective=effective, age_seconds=max(0, age) if age is not None else None)
    result["ready_for_scope"] = effective["admitted"] is True and effective["verified_working"] is True and effective["connected"] is True
    return result
