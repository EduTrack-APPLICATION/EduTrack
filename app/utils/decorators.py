"""
Decoradores de control de acceso por rol.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Solo accesible por administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def profesor_or_admin(f):
    """Accesible por profesores y administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_admin() or current_user.is_profesor()):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    """Solo accesible por super-administradores (desarrollador)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_super_admin():
            abort(404)  # 404 en vez de 403: no revelar que el endpoint existe
        return f(*args, **kwargs)
    return decorated_function
