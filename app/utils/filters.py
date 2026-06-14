
"""
Filtros Jinja personalizados y context processors.
"""
from datetime import datetime, date
from markupsafe import Markup
from app.utils.timezone import utc_to_cr


# ============================================================
# Constantes de localización en español
# ============================================================
MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre',
}

MESES_ABREV_ES = {
    1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr',
    5: 'may', 6: 'jun', 7: 'jul', 8: 'ago',
    9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic',
}

DIAS_ES = {
    0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
    4: 'viernes', 5: 'sábado', 6: 'domingo',
}


def init_filters(app):
    """Registra los filtros personalizados en la app Flask."""

    # ============================================================
    # Filtros de FECHA con zona horaria de Costa Rica
    # ============================================================

    @app.template_filter('fecha_cr')
    def fecha_cr_filter(dt, formato='%d/%m/%Y'):
        """Convierte datetime UTC a hora CR y formatea como fecha."""
        if dt is None:
            return '—'
        cr = utc_to_cr(dt) if hasattr(dt, 'hour') else dt
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
            return f'hace {int(seg / 60)} min'
        elif seg < 86400:
            return f'hace {int(seg / 3600)} h'
        elif seg < 172800:
            return 'ayer'
        elif seg < 604800:
            return f'hace {int(seg / 86400)} días'
        else:
            return utc_to_cr(dt).strftime('%d/%m/%Y')

    # ============================================================
    # Filtros en ESPAÑOL (mes, día semana, etc.)
    # ============================================================

    @app.template_filter('mes_es')
    def mes_es_filter(d):
        """Nombre del mes en español: 'junio'."""
        if d is None:
            return '—'
        return MESES_ES.get(d.month, '')

    @app.template_filter('mes_abrev_es')
    def mes_abrev_es_filter(d):
        """Mes abreviado en español: 'jun'."""
        if d is None:
            return '—'
        return MESES_ABREV_ES.get(d.month, '')

    @app.template_filter('dia_semana_es')
    def dia_semana_es_filter(d):
        """Día de la semana en español: 'lunes'."""
        if d is None:
            return '—'
        return DIAS_ES.get(d.weekday(), '')

    @app.template_filter('dia_mes_es')
    def dia_mes_es_filter(d):
        """Día + mes abreviado: '15 jun'."""
        if d is None:
            return '—'
        if hasattr(d, 'hour'):
            d = utc_to_cr(d).date()
        return f'{d.day} {MESES_ABREV_ES.get(d.month, "")}'

    @app.template_filter('fecha_larga_es')
    def fecha_larga_es_filter(d):
        """Fecha en español: 'lunes 14 de junio de 2026'."""
        if d is None:
            return '—'
        if hasattr(d, 'hour'):
            d = utc_to_cr(d).date()
        return f'{DIAS_ES[d.weekday()]} {d.day} de {MESES_ES[d.month]} de {d.year}'

    # ============================================================
    # Filtros GENÉRICOS (sin zona horaria — para campos `db.Date`)
    # ============================================================

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

    # ============================================================
    # Filtros de VISUALIZACIÓN (badges, iconos)
    # ============================================================

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

    # ============================================================
    # Context processors (variables globales en templates)
    # ============================================================

    @app.context_processor
    def inject_globals():
        from app.utils.timezone import now_cr
        return {
            'now_year': now_cr().year,
            'now_cr': now_cr,           # disponible como {{ now_cr() }}
        }


# Alias para compatibilidad (por si en algún lugar usas register_filters)
register_filters = init_filters
