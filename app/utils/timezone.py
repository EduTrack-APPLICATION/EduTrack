"""
Utilidades de zona horaria.
Costa Rica usa UTC-6 (Central Standard Time, sin horario de verano).
"""
from datetime import datetime, timezone, timedelta

# Costa Rica = UTC-6, todo el año
CR_TZ = timezone(timedelta(hours=-6))


def utc_to_cr(dt):
    """
    Convierte un datetime UTC (naive o aware) a hora de Costa Rica.
    Si recibe None, retorna None.
    """
    if dt is None:
        return None
    # Si no tiene timezone info, asumimos UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CR_TZ)


def now_cr():
    """Retorna la hora actual de Costa Rica."""
    return datetime.now(CR_TZ)


def now_utc():
    """Retorna la hora actual en UTC."""
    return datetime.now(timezone.utc)
