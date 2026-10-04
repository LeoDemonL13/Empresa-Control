from datetime import datetime, timezone


def _now_utc():
    return datetime.now(timezone.utc)
