"""
Cache simple en memoria para queries pesadas.
No requiere Redis ni configuración. Por usuario y por endpoint.
"""
import time
from functools import wraps
from flask import request
from flask_login import current_user


_cache = {}  # { key: (timestamp, valor) }
_MAX_ENTRIES = 200


def _purge_expired():
    """Limpia entradas vencidas. Llamado ocasionalmente."""
    if len(_cache) < _MAX_ENTRIES:
        return
    now = time.time()
    expired = [k for k, (t, _, ttl) in _cache.items() if now - t > ttl]
    for k in expired:
        _cache.pop(k, None)
    # Si sigue lleno, quitar el más viejo
    if len(_cache) >= _MAX_ENTRIES:
        oldest = min(_cache.items(), key=lambda x: x[1][0])
        _cache.pop(oldest[0], None)


def cached_view(seconds=60, by_user=True):
    """
    Cachea una vista por X segundos.
    Si by_user=True, la cache es separada por usuario.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Construir key
            if by_user and current_user.is_authenticated:
                key_base = f'{f.__module__}.{f.__name__}:user-{current_user.id}'
            else:
                key_base = f'{f.__module__}.{f.__name__}:anon'

            # Incluir query string en la key
            qs = request.query_string.decode('utf-8') if request else ''
            key = f'{key_base}?{qs}'

            # Buscar en cache
            entry = _cache.get(key)
            if entry:
                timestamp, value, ttl = entry
                if time.time() - timestamp < ttl:
                    return value

            # Ejecutar y guardar
            result = f(*args, **kwargs)
            _cache[key] = (time.time(), result, seconds)
            _purge_expired()
            return result
        return wrapper
    return decorator


def invalidate_user_cache(user_id=None):
    """Invalida la cache de un usuario específico (o todos si no se da)."""
    if user_id is None:
        _cache.clear()
        return
    prefix = f':user-{user_id}'
    keys_to_remove = [k for k in _cache if prefix in k]
    for k in keys_to_remove:
        _cache.pop(k, None)


def cache_stats():
    """Para debugging."""
    return {
        'entries': len(_cache),
        'max': _MAX_ENTRIES,
    }
