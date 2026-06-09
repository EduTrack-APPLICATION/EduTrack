"""
Dashboard principal con estadísticas y gráficos.
"""
from datetime import date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc

from app import db
from app.models import (
    Estudiante, Profesor, Grupo, Materia, Evaluacion, Nota, Asistencia,
    EstadoEstudianteEnum, EstadoAsistenciaEnum
)
from app.services.calculo_service import CalculoService
from app.utils.cache import cached_view

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
@cached_view(seconds=45, by_user=True)
def index():
    """Dashboard principal según rol."""
    # Filtro por profesor si es profesor
    profesor_id = None
    if current_user.is_profesor() and current_user.profesor:
        profesor_id = current_user.profesor.id

    # Estadísticas
    if profesor_id:
        # Profesor ve solo sus grupos
        grupos_qs = Grupo.query.filter_by(profesor_id=profesor_id, activo=True)
        total_grupos = grupos_qs.count()
        grupos_ids = [g.id for g in grupos_qs.all()]
        if grupos_ids:
            from app.models.grupo import EstudianteGrupo
            total_estudiantes = db.session.query(
                func.count(func.distinct(EstudianteGrupo.estudiante_id))
            ).filter(EstudianteGrupo.grupo_id.in_(grupos_ids)).scalar() or 0
        else:
            total_estudiantes = 0
        total_evaluaciones = Evaluacion.query.filter_by(profesor_id=profesor_id).count()
    else:
        # Admin ve todo
        total_grupos = Grupo.query.filter_by(activo=True).count()
        total_estudiantes = Estudiante.query.filter_by(
            estado=EstadoEstudianteEnum.ACTIVO.value).count()
        total_evaluaciones = Evaluacion.query.count()

    total_profesores = Profesor.query.filter_by(activo=True).count() if not profesor_id else None
    total_materias = Materia.query.filter_by(activa=True).count()

    # Promedio general
    promedio_general = CalculoService.promedio_general(profesor_id=profesor_id)

    # Estudiantes en riesgo
    en_riesgo = CalculoService.estudiantes_en_riesgo(profesor_id=profesor_id)
    total_riesgo = len(en_riesgo)

    # Actividad reciente
    actividad_reciente = Evaluacion.query
    if profesor_id:
        actividad_reciente = actividad_reciente.filter_by(profesor_id=profesor_id)
    actividad_reciente = actividad_reciente.order_by(desc(Evaluacion.fecha_creacion)).limit(8).all()

    # Próximas evaluaciones
    proximas = Evaluacion.query.filter(Evaluacion.fecha >= date.today())
    if profesor_id:
        proximas = proximas.filter(Evaluacion.profesor_id == profesor_id)
    proximas = proximas.order_by(Evaluacion.fecha).limit(5).all()

    # === Saludo contextual dinámico ===
    from datetime import datetime
    hora = datetime.now().hour
    if hora < 12:
        saludo, saludo_emoji = 'Buenos días', ''
    elif hora < 19:
        saludo, saludo_emoji = 'Buenas tardes', ''
    else:
        saludo, saludo_emoji = 'Buenas noches', ''

    # Día de la semana en español
    dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    hoy = date.today()
    fecha_legible = f"{dias[hoy.weekday()]} {hoy.day} de {meses[hoy.month - 1]}"

    # Tareas pendientes contextuales (lo que el usuario podría querer hacer)
    tareas = []

    if profesor_id:
        # Evaluaciones pasadas sin todas las notas registradas
        eval_pasadas = Evaluacion.query.filter(
            Evaluacion.profesor_id == profesor_id,
            Evaluacion.fecha <= hoy,
        ).all()

        sin_calificar = []
        for ev_obj in eval_pasadas:
            if ev_obj.grupo:
                total_est = ev_obj.grupo.estudiantes.count()
                con_nota = Nota.query.filter_by(evaluacion_id=ev_obj.id).count()
                if total_est > 0 and con_nota < total_est:
                    sin_calificar.append((ev_obj, total_est - con_nota))
        if sin_calificar:
            tareas.append({
                'icono': 'bi-clipboard-check',
                'color': 'warning',
                'texto': f'{len(sin_calificar)} '
                         f'{"evaluación" if len(sin_calificar) == 1 else "evaluaciones"} '
                         f'con notas pendientes',
                'url': '/evaluaciones/',
            })

        # Grupos sin asistencia tomada hoy
        grupos_propios = Grupo.query.filter_by(profesor_id=profesor_id, activo=True).all()
        grupos_sin_asist_hoy = [
            g for g in grupos_propios
            if not Asistencia.query.filter_by(grupo_id=g.id, fecha=hoy).first()
            and g.estudiantes.count() > 0
        ]
        if grupos_sin_asist_hoy:
            tareas.append({
                'icono': 'bi-calendar-x',
                'color': 'info',
                'texto': f'{len(grupos_sin_asist_hoy)} '
                         f'{"grupo sin asistencia" if len(grupos_sin_asist_hoy) == 1 else "grupos sin asistencia"} '
                         f'tomada hoy',
                'url': '/asistencia/',
            })

        # Evaluaciones próximas (en los próximos 7 días)
        proximas_semana = [e for e in proximas if (e.fecha - hoy).days <= 7]
        if proximas_semana:
            tareas.append({
                'icono': 'bi-calendar-event',
                'color': 'primary',
                'texto': f'{len(proximas_semana)} '
                         f'{"evaluación esta semana" if len(proximas_semana) == 1 else "evaluaciones esta semana"}',
                'url': '/evaluaciones/',
            })
    else:
        # Admin: cosas globales
        if total_riesgo > 0:
            tareas.append({
                'icono': 'bi-exclamation-triangle',
                'color': 'danger',
                'texto': f'{total_riesgo} '
                         f'{"estudiante en riesgo académico" if total_riesgo == 1 else "estudiantes en riesgo académico"}',
                'url': '/estudiantes/?estado=activo',
            })

        # Materias sin grupos
        materias_sin_grupos = [m for m in Materia.query.filter_by(activa=True).all()
                              if m.grupos.count() == 0]
        if materias_sin_grupos:
            tareas.append({
                'icono': 'bi-book',
                'color': 'warning',
                'texto': f'{len(materias_sin_grupos)} '
                         f'{"materia sin grupo asignado" if len(materias_sin_grupos) == 1 else "materias sin grupo asignado"}',
                'url': '/materias/',
            })

        # Grupos sin estudiantes
        grupos_vacios = [g for g in Grupo.query.filter_by(activo=True).all()
                        if g.estudiantes.count() == 0]
        if grupos_vacios:
            tareas.append({
                'icono': 'bi-people',
                'color': 'info',
                'texto': f'{len(grupos_vacios)} '
                         f'{"grupo sin estudiantes" if len(grupos_vacios) == 1 else "grupos sin estudiantes"} '
                         f'matriculados',
                'url': '/grupos/',
            })

    # Mensaje motivacional según situación
    if not tareas:
        mensaje_extra = '¡Todo al día! No tienes tareas pendientes.'
        mensaje_emoji = ''
    elif len(tareas) >= 3:
        mensaje_extra = 'Aquí tienes algunas tareas que requieren tu atención.'
        mensaje_emoji = ''
    else:
        mensaje_extra = 'Tienes algunas cosas pendientes.'
        mensaje_emoji = ''

    # === Stats de aprobación (para donut) ===
    aprobados = recuperacion = reprobados = sin_calificar = 0
    grupos_para_stats = (Grupo.query.filter_by(profesor_id=profesor_id, activo=True).all()
                         if profesor_id else
                         Grupo.query.filter_by(activo=True).all())
    for g in grupos_para_stats:
        for est in g.estudiantes:
            calc = CalculoService.nota_final_estudiante(est.id, g.id)
            if calc['evaluaciones_calificadas'] == 0:
                sin_calificar += 1
            else:
                nf = calc['nota_final']
                if nf >= 70:
                    aprobados += 1
                elif nf >= 60:
                    recuperacion += 1
                else:
                    reprobados += 1
    total_calificados = aprobados + recuperacion + reprobados
    pct_aprobacion = round(
        100 * aprobados / total_calificados, 1
    ) if total_calificados else 0

    # === Tira semanal (próximos 7 días) con evaluaciones ===
    semana = []
    dias_corto = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    for offset in range(7):
        d = hoy + timedelta(days=offset)
        evs_dia_qs = Evaluacion.query.filter(Evaluacion.fecha == d)
        if profesor_id:
            evs_dia_qs = evs_dia_qs.filter_by(profesor_id=profesor_id)
        evs_dia = evs_dia_qs.all()
        semana.append({
            'fecha': d,
            'dia_corto': dias_corto[d.weekday()],
            'dia_num': d.day,
            'mes_corto': meses[d.month - 1][:3].capitalize(),
            'es_hoy': (d == hoy),
            'es_finde': d.weekday() >= 5,
            'evaluaciones': evs_dia,
            'count': len(evs_dia),
        })

    # === Top 3 estudiantes (mejores) ===
    top_estudiantes = CalculoService.top_estudiantes(
        limite=3, periodo=None, anio=None,
    )
    # Si es profesor, filtrar a sus grupos
    if profesor_id:
        grupos_ids_set = {g.id for g in grupos_para_stats}
        ranking_full = CalculoService.top_estudiantes(limite=None)
        top_estudiantes = [
            r for r in ranking_full
            if any(g.id in grupos_ids_set for g, _ in r['grupos'])
        ][:3]
        # Re-numerar
        for i, it in enumerate(top_estudiantes, 1):
            it['posicion'] = i

    # === Tendencias para las stat cards (delta últimos 7 días) ===
    semana_atras = hoy - timedelta(days=7)

    # Estudiantes nuevos esta semana
    estudiantes_nuevos = Estudiante.query.filter(
        Estudiante.fecha_creacion >= semana_atras
    ).count()

    # Evaluaciones creadas esta semana
    eval_recientes_qs = Evaluacion.query.filter(
        Evaluacion.fecha_creacion >= semana_atras
    )
    if profesor_id:
        eval_recientes_qs = eval_recientes_qs.filter_by(profesor_id=profesor_id)
    eval_nuevas = eval_recientes_qs.count()

    # Porcentaje de evaluaciones calificadas (cuántas tienen notas)
    eval_calificadas = 0
    eval_pasadas = Evaluacion.query.filter(Evaluacion.fecha <= hoy)
    if profesor_id:
        eval_pasadas = eval_pasadas.filter_by(profesor_id=profesor_id)
    eval_pasadas_list = eval_pasadas.all()
    for ev_obj in eval_pasadas_list:
        if Nota.query.filter_by(evaluacion_id=ev_obj.id).count() > 0:
            eval_calificadas += 1
    pct_calificadas = round(100 * eval_calificadas / len(eval_pasadas_list)) \
        if eval_pasadas_list else 0

    # === DATOS PARA EL NUEVO DASHBOARD ===

    # 1. Eventos de HOY específicamente
    eval_hoy_qs = Evaluacion.query.filter(Evaluacion.fecha == hoy)
    if profesor_id:
        eval_hoy_qs = eval_hoy_qs.filter_by(profesor_id=profesor_id)
    eval_hoy = eval_hoy_qs.all()

    # 2. Promedio últimos 7 días vs anterior (delta real)
    notas_recientes = db.session.query(func.avg(Nota.puntaje)).filter(
        Nota.fecha_actualizacion >= hoy - timedelta(days=7)
    ).scalar() or 0
    notas_anteriores = db.session.query(func.avg(Nota.puntaje)).filter(
        Nota.fecha_actualizacion >= hoy - timedelta(days=14),
        Nota.fecha_actualizacion < hoy - timedelta(days=7)
    ).scalar() or 0
    delta_promedio = round(float(notas_recientes) - float(notas_anteriores), 1)

    # 3. Mini sparkline de las últimas 7 jornadas de notas (lista de 7 valores)
    sparkline_notas = []
    for offset in range(6, -1, -1):
        dia = hoy - timedelta(days=offset)
        avg = db.session.query(func.avg(Nota.puntaje)).filter(
            func.date(Nota.fecha_actualizacion) == dia
        ).scalar()
        sparkline_notas.append(round(float(avg), 1) if avg else None)

    # 4. Mini sparkline de asistencia últimos 7 días
    sparkline_asistencia = []
    for offset in range(6, -1, -1):
        dia = hoy - timedelta(days=offset)
        total_dia = Asistencia.query.filter(Asistencia.fecha == dia).count()
        presentes_dia = Asistencia.query.filter(
            Asistencia.fecha == dia,
            Asistencia.estado == EstadoAsistenciaEnum.PRESENTE.value
        ).count()
        pct = round(100 * presentes_dia / total_dia) if total_dia else None
        sparkline_asistencia.append(pct)

    # 5. Asistencia de HOY
    asis_hoy_total = Asistencia.query.filter(Asistencia.fecha == hoy).count()
    asis_hoy_presentes = Asistencia.query.filter(
        Asistencia.fecha == hoy,
        Asistencia.estado == EstadoAsistenciaEnum.PRESENTE.value
    ).count()
    pct_asis_hoy = round(100 * asis_hoy_presentes / asis_hoy_total) if asis_hoy_total else None

    # 6. Próxima evaluación más cercana
    proxima_eval = Evaluacion.query.filter(Evaluacion.fecha > hoy).order_by(
        Evaluacion.fecha.asc()
    ).first()
    dias_proxima = (proxima_eval.fecha - hoy).days if proxima_eval else None

    return render_template(
        'dashboard/index.html',
        total_estudiantes=total_estudiantes,
        total_profesores=total_profesores,
        total_grupos=total_grupos,
        total_materias=total_materias,
        total_evaluaciones=total_evaluaciones,
        promedio_general=promedio_general,
        total_riesgo=total_riesgo,
        en_riesgo=en_riesgo[:5],
        actividad_reciente=actividad_reciente,
        proximas=proximas,
        saludo=saludo,
        saludo_emoji=saludo_emoji,
        fecha_legible=fecha_legible,
        tareas_pendientes=tareas,
        mensaje_extra=mensaje_extra,
        mensaje_emoji=mensaje_emoji,
        aprobados=aprobados,
        recuperacion=recuperacion,
        reprobados=reprobados,
        sin_calificar=sin_calificar,
        total_calificados=total_calificados,
        pct_aprobacion=pct_aprobacion,
        semana=semana,
        top_estudiantes=top_estudiantes,
        hoy=hoy,
        estudiantes_nuevos=estudiantes_nuevos,
        eval_nuevas=eval_nuevas,
        pct_calificadas=pct_calificadas,
        # Datos nuevos para el rediseño
        eval_hoy=eval_hoy,
        delta_promedio=delta_promedio,
        sparkline_notas=sparkline_notas,
        sparkline_asistencia=sparkline_asistencia,
        pct_asis_hoy=pct_asis_hoy,
        asis_hoy_total=asis_hoy_total,
        proxima_eval=proxima_eval,
        dias_proxima=dias_proxima,
    )


@dashboard_bp.route('/api/grafico/notas-distribucion')
@login_required
def grafico_distribucion_notas():
    """Distribución de notas para Chart.js."""
    profesor_id = current_user.profesor.id if current_user.is_profesor() and current_user.profesor else None

    rangos = {
        '0-39': 0, '40-59': 0, '60-69': 0, '70-79': 0, '80-89': 0, '90-100': 0
    }

    query = db.session.query(
        (Nota.puntaje * 100.0 / Evaluacion.puntaje_maximo).label('pct')
    ).select_from(Nota).join(Evaluacion, Nota.evaluacion_id == Evaluacion.id)
    if profesor_id:
        query = query.filter(Evaluacion.profesor_id == profesor_id)

    for row in query.all():
        pct = row.pct or 0
        if pct < 40:
            rangos['0-39'] += 1
        elif pct < 60:
            rangos['40-59'] += 1
        elif pct < 70:
            rangos['60-69'] += 1
        elif pct < 80:
            rangos['70-79'] += 1
        elif pct < 90:
            rangos['80-89'] += 1
        else:
            rangos['90-100'] += 1

    return jsonify({
        'labels': list(rangos.keys()),
        'data': list(rangos.values()),
    })


@dashboard_bp.route('/api/grafico/asistencia-semanal')
@login_required
def grafico_asistencia_semanal():
    """Asistencia de los últimos 14 días."""
    profesor_id = current_user.profesor.id if current_user.is_profesor() and current_user.profesor else None

    labels = []
    presentes = []
    ausentes = []

    hoy = date.today()
    for i in range(13, -1, -1):
        f = hoy - timedelta(days=i)
        labels.append(f.strftime('%d/%m'))
        q = db.session.query(Asistencia).filter(Asistencia.fecha == f)
        if profesor_id:
            q = q.join(Grupo, Asistencia.grupo_id == Grupo.id).filter(
                Grupo.profesor_id == profesor_id)

        pres = q.filter(Asistencia.estado.in_([
            EstadoAsistenciaEnum.PRESENTE.value,
            EstadoAsistenciaEnum.TARDIA.value,
            EstadoAsistenciaEnum.JUSTIFICADO.value
        ])).count()
        aus = q.filter(Asistencia.estado == EstadoAsistenciaEnum.AUSENTE.value).count()

        presentes.append(pres)
        ausentes.append(aus)

    return jsonify({
        'labels': labels,
        'presentes': presentes,
        'ausentes': ausentes,
    })
