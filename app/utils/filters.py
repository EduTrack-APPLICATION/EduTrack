"""
Filtros Jinja personalizados y context processors.
"""
from datetime import datetime, date
from markupsafe import Markup
from app.utils.timezone import utc_to_c

"""Filtros personalizados de Jinja para EduTrack."""
from app.utils.timezone import utc_to_cr


def init_filters(app):
    """Registra los filtros personalizados en la app Flask."""

    @app.template_filter('fecha_cr')
    def fecha_cr_filter(dt, formato='%d/%m/%Y'):
        """Convierte datetime UTC a hora CR y formatea como fecha."""
        if dt is None:
            return '—'
        cr = utc_to_cr(dt)
        return cr.strftime(formato)

    @app.template_filter('fecha_hora_cr')
    def fecha_hora_cr_filter(dt, formato='%d/%m/%Y %H:%M'):
        """Convierte datetime UTC a hora CR y formatea como fecha y hora."""
        if dt is None:
            return '—'
        cr = utc_to_cr(dt)
        return cr.strftime(formato)

    @app.template_filter('hora_cr')
    def hora_cr_filter(dt, formato='%H:%M'):
        """Convierte datetime UTC a hora CR y formatea solo la hora."""
        if dt is None:
            return '—'
        cr = utc_to_cr(dt)
        return cr.strftime(formato)

    @app.template_filter('relativo_cr')
    def relativo_cr_filter(dt):
        """Retorna tiempo relativo: 'hace 5 minutos', 'ayer', etc."""
        if dt is None:
            return '—'
        from datetime import datetime, timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ahora = datetime.now(timezone.utc)
        diff = ahora - dt
        seg = diff.total_seconds()

        if seg < 60:
            return 'hace un momento'
        elif seg < 3600:
            min = int(seg / 60)
            return f'hace {min} min'
        elif seg < 86400:
            hrs = int(seg / 3600)
            return f'hace {hrs} h'
        elif seg < 172800:
            return 'ayer'
        elif seg < 604800:
            dias = int(seg / 86400)
            return f'hace {dias} días'
        else:
            return utc_to_cr(dt).strftime('%d/%m/%Y')
            

def register_filters(app):
    @app.template_filter('fecha')
    def fecha_filter(value, formato='%d/%m/%Y'):
        if value is None:
            return ''
        if isinstance(value, (datetime, date)):
            return value.strftime(formato)
        return str(value)

    @app.template_filter('fechahora')
    def fechahora_filter(value):
        if value is None:
            return ''
        return value.strftime('%d/%m/%Y %H:%M')

    @app.template_filter('nota')
    def nota_filter(value, decimales=2):
        """Retorna la nota formateada como badge HTML con color según rango."""
        if value is None:
            return Markup('<span class="text-muted">—</span>')
        try:
            n = float(value)
        except (ValueError, TypeError):
            return Markup('<span class="text-muted">—</span>')

        if n >= 70:
            color = 'success'
        elif n >= 60:
            color = 'warning'
        else:
            color = 'danger'

        return Markup(
            f'<span class="badge bg-{color}-subtle text-{color} fw-bold" '
            f'style="font-size:0.9rem;">{n:.{decimales}f}</span>'
        )

    @app.template_filter('badge_estado')
    def badge_estado_filter(estado):
        """Retorna un badge HTML para el estado."""
        mapping = {
            'activo':       ('success',   'Activo'),
            'inactivo':     ('secondary', 'Inactivo'),
            'graduado':     ('info',      'Graduado'),
            'retirado':     ('dark',      'Retirado'),
            'aprobado':     ('success',   'Aprobado'),
            'reprobado':    ('danger',    'Reprobado'),
            'recuperacion': ('warning',   'Recuperación'),
            'presente':     ('success',   'Presente'),
            'ausente':      ('danger',    'Ausente'),
            'justificado':  ('info',      'Justificado'),
            'tardia':       ('warning',   'Tardía'),
        }
        color, label = mapping.get(estado, ('secondary', str(estado or '—').capitalize()))
        return Markup(
            f'<span class="badge bg-{color}-subtle text-{color}">{label}</span>'
        )

    @app.template_filter('icono_tipo')
    def icono_tipo_filter(tipo):
        """Retorna el icono Bootstrap Icons para un tipo de evaluación."""
        mapping = {
            'examen':        'bi-file-earmark-text',
            'quiz':          'bi-patch-question',
            'tarea':         'bi-pencil-square',
            'proyecto':      'bi-folder',
            'exposicion':    'bi-easel',
            'practica':      'bi-laptop',
            'participacion': 'bi-people',
        }
        icon = mapping.get(tipo, 'bi-file-earmark')
        return Markup(f'<i class="bi {icon} text-primary"></i>')

    # ===== Context processors =====
    @app.context_processor
    def inject_globals():
        return {
            'now_year': datetime.now().year,
        }
