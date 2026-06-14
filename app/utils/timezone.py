# app/utils/timezone.py
from datetime import datetime, timezone, timedelta
CR_TZ = timezone(timedelta(hours=-6))

def now_cr():
    return datetime.now(CR_TZ)
