"""
Portal del estudiante.
Vista de solo lectura para que cada estudiante consulte SUS datos.
Aislamiento estricto: nunca ve datos de otros estudiantes.
"""
from datetime import date, datetime, timedelta
from collections import defaultdict

from flask import Blueprint, render_template, abort, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    Estudiante, EstudianteGrupo, Grupo, Materia, Evaluacion,
    Nota, Asistencia, EstadoAsistenciaEnum
)
from app.utils.decorators import estudiante_required


portal_bp = Blueprint('portal', __name__)


def _get_mi_estudiante():
    """Retorna el Estudiante asociado al usuario actual."""
    if not current_user.is_estudiante() or not current_user.estudiante_id:
        abort(403)
    est = Estudiante.query.get(current_user.estudiante_id)
    if not est or est.eliminado_en:
        abort(404)
    return est


@portal_bp.route('/')
@login_required
@estudiante_required
def index():
    """Dashboard del estudiante: resumen + KPIs."""
    estudiante = _get_mi_estudiante()

    # Grupos del estudiante (carga eficiente con joinedload)
    mis_grupos = (
        db.session.query(Grupo)
        .join(EstudianteGrupo, EstudianteGrupo.grupo_id == Grupo.id)
        .filter(
            EstudianteGrupo.estudiante_id == estudiante.id,
            EstudianteGrupo.activa == True,
        )
        .options(joinedload(Grupo.materia), joinedload(Grupo.profesor_titular))
        .all()
    )

    # Promedios por materia
    promedios = []
    suma_total = 0
    count_total = 0
    for grupo in mis_grupos:
        notas = (
            Nota.query
            .filter_by(estudiante_id=estudiante.id)
            .join(Evaluacion, Nota.evaluacion_id == Evaluacion.id)
            .filter(Evaluacion.grupo_id == grupo.id)
            .all()
        )
        if notas:
            # Promedio ponderado por porcentaje
            suma_p = 0
            peso_total = 0
            for n in notas:
                if n.evaluacion and n.puntaje is not None:
                    # Normalizar a 0-100
                    pct = (n.puntaje / n.evaluacion.puntaje_maximo) * 100
                    peso = n.evaluacion.porcentaje or 10
                    suma_p += pct * peso
                    peso_total += peso
            if peso_total > 0:
                promedio = round(suma_p / peso_total, 1)
                promedios.append({
                    'materia': grupo.materia.nombre if grupo.materia else '—',
                    'grupo_codigo': grupo.codigo,
                    'profesor': grupo.profesor_titular.nombre_completo if grupo.profesor_titular else '—',
                    'promedio': promedio,
                    'num_notas': len(notas),
                    'estado': 'aprobado' if promedio >= 70 else
                              ('recuperacion' if promedio >= 60 else 'reprobado'),
                })
                suma_total += promedio
                count_total += 1

    promedio_general = round(suma_total / count_total, 1) if count_total else 0

    # Asistencia general (% de días presentes)
    total_asistencias = Asistencia.query.filter_by(estudiante_id=estudiante.id).count()
    presentes = Asistencia.query.filter_by(
        estudiante_id=estudiante.id,
        estado=EstadoAsistenciaEnum.PRESENTE.value,
    ).count()
    pct_asistencia = round((presentes / total_asistencias) * 100, 1) if total_asistencias else 0

    # Próximas evaluaciones (de sus grupos)
    grupo_ids = [g.id for g in mis_grupos]
    proximas = []
    if grupo_ids:
        proximas = (
            Evaluacion.query
            .filter(
                Evaluacion.grupo_id.in_(grupo_ids),
                Evaluacion.fecha >= date.today(),
            )
            .options(joinedload(Evaluacion.materia))
            .order_by(Evaluacion.fecha.asc())
            .limit(5)
            .all()
        )

    return render_template(
        'portal/index.html',
        estudiante=estudiante,
        promedios=promedios,
        promedio_general=promedio_general,
        pct_asistencia=pct_asistencia,
        num_materias=len(mis_grupos),
        proximas=proximas,
    )


@portal_bp.route('/notas')
@login_required
@estudiante_required
def notas():
    """Vista detallada de notas por materia."""
    estudiante = _get_mi_estudiante()

    mis_grupos = (
        db.session.query(Grupo)
        .join(EstudianteGrupo, EstudianteGrupo.grupo_id == Grupo.id)
        .filter(
            EstudianteGrupo.estudiante_id == estudiante.id,
            EstudianteGrupo.activa == True,
        )
        .options(joinedload(Grupo.materia))
        .all()
    )

    # Estructura: lista de { grupo, materia, notas: [...], promedio }
    detalle = []
    for grupo in mis_grupos:
        evaluaciones = (
            Evaluacion.query
            .filter_by(grupo_id=grupo.id)
            .order_by(Evaluacion.fecha.desc())
            .all()
        )
        items = []
        suma_p = 0
        peso_total = 0
        for ev in evaluaciones:
            nota = Nota.query.filter_by(
                estudiante_id=estudiante.id,
                evaluacion_id=ev.id,
            ).first()
      if nota and nota.puntaje is not None:
    pct = round((nota.puntaje / ev.puntaje_maximo) * 100, 1)
    suma_p += pct * (ev.porcentaje or 10)
    peso_total += (ev.porcentaje or 10)
    items.append({
        'evaluacion': ev,
        'nota_obtenida': nota.puntaje,
        'porcentaje_obtenido': pct,
        'fecha': ev.fecha,
        'tiene_nota': True,
        'observaciones': nota.observaciones,  # ← AGREGADO
    })
else:
    items.append({
        'evaluacion': ev,
        'nota_obtenida': None,
        'porcentaje_obtenido': None,
        'fecha': ev.fecha,
        'tiene_nota': False,
        'observaciones': None,  # ← AGREGADO
    })

    return render_template('portal/notas.html',
                            estudiante=estudiante, detalle=detalle)


@portal_bp.route('/asistencia')
@login_required
@estudiante_required
def asistencia():
    """Vista de asistencia con heatmap mensual."""
    estudiante = _get_mi_estudiante()

    # Asistencias últimos 90 días
    desde = date.today() - timedelta(days=90)
    registros = (
        Asistencia.query
        .filter(
            Asistencia.estudiante_id == estudiante.id,
            Asistencia.fecha >= desde,
        )
        .order_by(Asistencia.fecha.desc())
        .all()
    )

    # Agrupar por fecha (puede haber varios grupos el mismo día)
    por_dia = defaultdict(list)
    for r in registros:
        por_dia[r.fecha.isoformat()].append(r.estado)

    # Resumen por estado
    conteo = defaultdict(int)
    for r in registros:
        conteo[r.estado] += 1
    total = len(registros)

    # Días del heatmap (últimos 90)
    dias_heatmap = []
    for i in range(89, -1, -1):
        d = date.today() - timedelta(days=i)
        estados_dia = por_dia.get(d.isoformat(), [])
        if not estados_dia:
            categoria = 'sin-registro'
        elif all(e == EstadoAsistenciaEnum.PRESENTE.value for e in estados_dia):
            categoria = 'presente'
        elif any(e == EstadoAsistenciaEnum.AUSENTE.value for e in estados_dia):
            categoria = 'ausente'
        else:
            categoria = 'parcial'  # tarde o justificada
        dias_heatmap.append({
            'fecha': d,
            'categoria': categoria,
            'estados': estados_dia,
        })

    return render_template(
        'portal/asistencia.html',
        estudiante=estudiante,
        dias_heatmap=dias_heatmap,
        conteo=dict(conteo),
        total=total,
        EstadoAsistenciaEnum=EstadoAsistenciaEnum,
    )


# ============================================================
# Redirección automática: si un estudiante intenta entrar al
# dashboard normal, lo mandamos al portal.
# Esta función se llama desde main.py / dashboard.py vía blueprint.before_request.
# ============================================================
def redirect_if_estudiante():
    """Llamado como before_request global."""
    if current_user.is_authenticated and current_user.is_estudiante():
        from flask import request
        # Permitir solo portal, auth, static
        path = request.path
        if (path.startswith('/portal') or path.startswith('/auth') or
            path.startswith('/static')):
            return None
        return redirect(url_for('portal.index'))
    return None
