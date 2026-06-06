"""
Panel de desarrollador (super_admin).
- Diagnóstico del sistema
- Estadísticas de BD
- Acciones de mantenimiento
- Feature flags
"""
import os
import sys
import platform
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, text

from app import db
from app.models import (
    Usuario, Estudiante, Profesor, Materia, Grupo, Evaluacion,
    Nota, Asistencia, IntentoLogin, Configuracion
)
from app.utils.decorators import super_admin_required

dev_bp = Blueprint('dev', __name__)


# Tiempo de inicio del servidor (para uptime)
_SERVER_START = datetime.utcnow()


def _format_uptime():
    delta = datetime.utcnow() - _SERVER_START
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    parts = []
    if days: parts.append(f'{days}d')
    if hours: parts.append(f'{hours}h')
    parts.append(f'{minutes}m')
    return ' '.join(parts)


@dev_bp.route('/')
@login_required
@super_admin_required
def index():
    """Dashboard principal del developer."""

    # === System info ===
    system_info = {
        'python_version': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
        'platform': platform.system() + ' ' + platform.release(),
        'flask_env': current_app.config.get('ENV', os.environ.get('FLASK_ENV', 'unknown')),
        'debug': current_app.debug,
        'uptime': _format_uptime(),
        'server_start': _SERVER_START.strftime('%Y-%m-%d %H:%M:%S'),
    }

    # === Database ===
    db_url = str(current_app.config.get('SQLALCHEMY_DATABASE_URI', ''))
    if 'postgresql' in db_url:
        db_type = 'PostgreSQL'
    elif 'sqlite' in db_url:
        db_type = 'SQLite'
    else:
        db_type = 'Otro'

    # Ocultar credenciales en la URL
    db_url_safe = db_url
    if '@' in db_url_safe:
        # postgresql://user:pass@host/db → postgresql://user:***@host/db
        prefix, rest = db_url_safe.split('://', 1)
        if ':' in rest.split('@')[0]:
            user_part, host_part = rest.split('@', 1)
            user, _ = user_part.split(':', 1)
            db_url_safe = f'{prefix}://{user}:***@{host_part}'

    # === DB stats ===
    db_stats = []
    tablas = [
        ('Usuarios', Usuario),
        ('Estudiantes', Estudiante),
        ('Profesores', Profesor),
        ('Materias', Materia),
        ('Grupos', Grupo),
        ('Evaluaciones', Evaluacion),
        ('Notas', Nota),
        ('Asistencias', Asistencia),
        ('Intentos de login', IntentoLogin),
        ('Configuración', Configuracion),
    ]
    for nombre, modelo in tablas:
        try:
            count = modelo.query.count()
        except Exception:
            count = 0
        db_stats.append({'nombre': nombre, 'count': count})

    # === Stats adicionales ===
    estudiantes_papelera = Estudiante.query.filter(
        Estudiante.eliminado_en.isnot(None)
    ).count()

    intentos_24h = IntentoLogin.query.filter(
        IntentoLogin.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).count()

    # === Email ===
    email_config = {
        'enabled': current_app.config.get('MAIL_ENABLED', False),
        'server': current_app.config.get('MAIL_SERVER', '—'),
        'port': current_app.config.get('MAIL_PORT', 0),
    }

    # === Feature flags ===
    flags = Configuracion.all_flags()

    # === Recent errors (de logs en memoria, si los hay) ===
    recent_errors = _get_recent_errors()

    return render_template(
        'dev/index.html',
        system_info=system_info,
        db_type=db_type,
        db_url_safe=db_url_safe,
        db_stats=db_stats,
        estudiantes_papelera=estudiantes_papelera,
        intentos_24h=intentos_24h,
        email_config=email_config,
        flags=flags,
        recent_errors=recent_errors,
    )


@dev_bp.route('/feature-flags', methods=['POST'])
@login_required
@super_admin_required
def toggle_flag():
    """Activar/desactivar feature flag."""
    clave = request.form.get('clave', '').strip()
    if clave not in Configuracion.DEFAULTS:
        flash('Feature flag desconocido.', 'danger')
        return redirect(url_for('dev.index'))

    valor_actual = Configuracion.get_bool(clave)
    nuevo = not valor_actual
    Configuracion.set(clave, 'true' if nuevo else 'false')

    flash(f'Flag "{clave}" {"activado" if nuevo else "desactivado"}.', 'success')
    return redirect(url_for('dev.index'))


@dev_bp.route('/mantenimiento/vaciar-papelera', methods=['POST'])
@login_required
@super_admin_required
def vaciar_papelera():
    """Elimina permanentemente todos los estudiantes en la papelera."""
    eliminados = Estudiante.query.filter(
        Estudiante.eliminado_en.isnot(None)
    ).all()
    n = len(eliminados)
    for e in eliminados:
        db.session.delete(e)
    db.session.commit()
    flash(f'Papelera vaciada: {n} registro{"" if n == 1 else "s"} eliminado{"" if n == 1 else "s"} permanentemente.',
          'info')
    return redirect(url_for('dev.index'))


@dev_bp.route('/mantenimiento/limpiar-logs', methods=['POST'])
@login_required
@super_admin_required
def limpiar_logs():
    """Borra intentos de login con más de 6 meses de antigüedad."""
    limite = datetime.utcnow() - timedelta(days=180)
    eliminados = IntentoLogin.query.filter(
        IntentoLogin.timestamp < limite
    ).delete(synchronize_session=False)
    db.session.commit()
    flash(f'{eliminados} registro{"" if eliminados == 1 else "s"} de auditoría '
          f'antiguo{"" if eliminados == 1 else "s"} eliminado{"" if eliminados == 1 else "s"}.',
          'success')
    return redirect(url_for('dev.index'))


@dev_bp.route('/mantenimiento/forzar-logout-todos', methods=['POST'])
@login_required
@super_admin_required
def forzar_logout_todos():
    """Resetea ultimo_login de todos los usuarios — efectivamente fuerza re-autenticación
    en algunos sistemas; al menos deja registro y rotación de SECRET_KEY haría el resto."""
    # Para forzar logout real necesitaríamos rotar SECRET_KEY o invalidar sesiones.
    # Aquí simplemente reseteamos contadores y logueamos la acción.
    actualizados = Usuario.query.update({'intentos_fallidos': 0, 'bloqueado_hasta': None})
    db.session.commit()
    flash(f'Contadores de seguridad reseteados en {actualizados} usuario'
          f'{"" if actualizados == 1 else "s"}. '
          f'Para forzar logout real, rota el SECRET_KEY en .env y reinicia el servidor.',
          'info')
    return redirect(url_for('dev.index'))


@dev_bp.route('/mantenimiento/test-email', methods=['POST'])
@login_required
@super_admin_required
def test_email():
    """Envía un email de prueba a la cuenta del super_admin actual."""
    from app.services.email_service import enviar_email

    if not current_user.email:
        flash('Tu cuenta no tiene email configurado.', 'warning')
        return redirect(url_for('dev.index'))

    html = '''<h2>Email de prueba</h2>
              <p>Este email confirma que la configuración SMTP de EduTrack funciona.</p>
              <p>Enviado el: ''' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC</p>'
    text = f'Email de prueba enviado el {datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC.'

    ok = enviar_email(
        to=current_user.email,
        subject='[EduTrack] Test de configuración SMTP',
        html=html,
        text=text,
    )

    if ok and current_app.config.get('MAIL_ENABLED'):
        flash(f'Email de prueba enviado a {current_user.email}. Revisa tu bandeja.', 'success')
    elif ok:
        flash('Email impreso en la consola del servidor (MAIL_ENABLED=False). '
              'Configura MAIL_USERNAME y MAIL_PASSWORD en .env para envío real.',
              'info')
    else:
        flash('Error al enviar el email. Revisa la consola del servidor.', 'danger')
    return redirect(url_for('dev.index'))


# ============================================================
# Helpers — captura de errores recientes
# ============================================================
_recent_errors = []  # buffer en memoria
_MAX_ERRORS = 20


def _get_recent_errors():
    """Retorna los últimos 20 errores capturados."""
    return list(reversed(_recent_errors[-_MAX_ERRORS:]))


def init_error_capture(app):
    """Engancha un handler que captura errores 500 en memoria."""
    @app.errorhandler(Exception)
    def _capture(e):
        # Solo capturar excepciones no manejadas (500)
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException) and e.code < 500:
            return None  # dejar pasar al handler normal
        try:
            _recent_errors.append({
                'timestamp': datetime.utcnow(),
                'type': type(e).__name__,
                'message': str(e)[:200],
                'path': request.path if request else '?',
            })
            # Limitar memoria
            if len(_recent_errors) > _MAX_ERRORS * 2:
                del _recent_errors[:_MAX_ERRORS]
        except Exception:
            pass
        # Re-lanzar para que el handler normal de Flask lo procese
        raise e
