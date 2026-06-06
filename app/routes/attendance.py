"""
Rutas de Asistencia: registro rápido por grupo y fecha.
"""
from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Asistencia, Grupo, EstadoAsistenciaEnum
from app.utils.decorators import profesor_or_admin

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/')
@login_required
@profesor_or_admin
def listar():
    """Listado de grupos para tomar asistencia."""
    query = Grupo.query.filter_by(activo=True)
    if current_user.is_profesor() and current_user.profesor:
        query = query.filter_by(profesor_id=current_user.profesor.id)
    grupos = query.order_by(Grupo.codigo).all()
    return render_template('attendance/listar.html', grupos=grupos)


@attendance_bp.route('/grupo/<int:grupo_id>', methods=['GET', 'POST'])
@login_required
@profesor_or_admin
def tomar(grupo_id):
    """Toma de asistencia para una fecha específica."""
    grupo = Grupo.query.get_or_404(grupo_id)

    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('attendance.listar'))

    fecha_str = request.args.get('fecha') or request.form.get('fecha')
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
    except ValueError:
        fecha = date.today()

    if request.method == 'POST':
        registrados = 0
        for est in grupo.estudiantes:
            estado_val = request.form.get(f'estado_{est.id}', EstadoAsistenciaEnum.PRESENTE.value)
            obs = request.form.get(f'obs_{est.id}', '').strip() or None

            asist = Asistencia.query.filter_by(
                estudiante_id=est.id, grupo_id=grupo.id, fecha=fecha
            ).first()

            if asist:
                asist.estado = estado_val
                asist.observaciones = obs
            else:
                asist = Asistencia(
                    estudiante_id=est.id, grupo_id=grupo.id,
                    fecha=fecha, estado=estado_val, observaciones=obs,
                )
                db.session.add(asist)
            registrados += 1

        db.session.commit()
        flash(f'✓ Asistencia del {fecha.strftime("%d/%m/%Y")} registrada ({registrados} estudiantes).',
              'success')
        return redirect(url_for('attendance.tomar', grupo_id=grupo_id, fecha=fecha.isoformat()))

    estudiantes = list(grupo.estudiantes.order_by('apellido'))
    asistencias_dict = {
        a.estudiante_id: a
        for a in Asistencia.query.filter_by(grupo_id=grupo.id, fecha=fecha).all()
    }

    items = []
    for est in estudiantes:
        a = asistencias_dict.get(est.id)
        items.append({
            'estudiante': est,
            'estado': a.estado if a else EstadoAsistenciaEnum.PRESENTE.value,
            'observaciones': a.observaciones if a else '',
        })

    return render_template(
        'attendance/tomar.html',
        grupo=grupo, items=items, fecha=fecha,
        estados=[
            (EstadoAsistenciaEnum.PRESENTE.value, 'Presente', 'success'),
            (EstadoAsistenciaEnum.AUSENTE.value, 'Ausente', 'danger'),
            (EstadoAsistenciaEnum.JUSTIFICADO.value, 'Justificado', 'info'),
            (EstadoAsistenciaEnum.TARDIA.value, 'Tardía', 'warning'),
        ],
    )


@attendance_bp.route('/grupo/<int:grupo_id>/historial')
@login_required
@profesor_or_admin
def historial(grupo_id):
    """Historial de asistencia del grupo."""
    grupo = Grupo.query.get_or_404(grupo_id)

    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('attendance.listar'))

    # Fechas únicas con asistencia
    from sqlalchemy import distinct
    fechas = [r[0] for r in db.session.query(distinct(Asistencia.fecha))
              .filter_by(grupo_id=grupo_id).order_by(Asistencia.fecha.desc()).all()]

    # Matriz: estudiante -> {fecha: estado}
    estudiantes = list(grupo.estudiantes.order_by('apellido'))
    asistencias = Asistencia.query.filter_by(grupo_id=grupo_id).all()

    matriz = {est.id: {} for est in estudiantes}
    for a in asistencias:
        if a.estudiante_id in matriz:
            matriz[a.estudiante_id][a.fecha] = a.estado

    from app.services.calculo_service import CalculoService
    porcentajes = {est.id: CalculoService.porcentaje_asistencia(est.id, grupo_id)
                   for est in estudiantes}

    return render_template('attendance/historial.html',
                           grupo=grupo, estudiantes=estudiantes,
                           fechas=fechas, matriz=matriz, porcentajes=porcentajes)
