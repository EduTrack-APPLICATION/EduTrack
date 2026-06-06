"""
Filtros Jinja personalizados y context processors.
"""
from datetime import datetime, date
from markupsafe import Markup


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
