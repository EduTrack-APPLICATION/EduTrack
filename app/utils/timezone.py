# app/utils/timezone.py
from datetime import datetime, timezone, timedelta
CR_TZ = timezone(timedelta(hours=-6))


def now_cr():
    return datetime.now(CR_TZ)


def utc_to_cr(dt):
    """Convierte un datetime UTC a hora de Costa Rica (UTC-6)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CR_TZ)
