"""
Rutas de Reportes: PDF, Excel, Boletines.
"""
from flask import Blueprint, render_template, send_file, flash, redirect, url_for, request
from flask_login import login_required, current_user

from app.models import Estudiante, Grupo
from app.services.reporte_service import ReporteService
from app.utils.decorators import profesor_or_admin

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@login_required
@profesor_or_admin
def index():
    """Página principal de reportes."""
    grupos_q = Grupo.query.filter_by(activo=True)
    if current_user.is_profesor() and current_user.profesor:
        grupos_q = grupos_q.filter_by(profesor_id=current_user.profesor.id)
    grupos = grupos_q.order_by(Grupo.codigo).all()
    return render_template('reports/index.html', grupos=grupos)


@reports_bp.route('/boletin/<int:estudiante_id>')
@reports_bp.route('/boletin/<int:estudiante_id>/grupo/<int:grupo_id>')
@login_required
@profesor_or_admin
def boletin(estudiante_id, grupo_id=None):
    """Boletín PDF de un estudiante."""
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    grupo = Grupo.query.get(grupo_id) if grupo_id else None

    if current_user.is_profesor() and current_user.profesor:
        if grupo is not None:
            if grupo.profesor_id != current_user.profesor.id:
                flash('Sin permisos.', 'danger')
                return redirect(url_for('reports.index'))
        elif not any(g.profesor_id == current_user.profesor.id for g in estudiante.grupos):
            flash('Sin permisos.', 'danger')
            return redirect(url_for('reports.index'))

    buf = ReporteService.boletin_estudiante(estudiante, grupo=grupo)
    filename = f'boletin_{estudiante.codigo}.pdf'
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


@reports_bp.route('/grupo/<int:grupo_id>/pdf')
@login_required
@profesor_or_admin
def grupo_pdf(grupo_id):
    """Reporte PDF de un grupo completo."""
    grupo = Grupo.query.get_or_404(grupo_id)

    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('reports.index'))

    buf = ReporteService.reporte_grupo_pdf(grupo)
    filename = f'reporte_{grupo.codigo}.pdf'
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


@reports_bp.route('/grupo/<int:grupo_id>/excel')
@login_required
@profesor_or_admin
def grupo_excel(grupo_id):
    """Excel con notas del grupo."""
    grupo = Grupo.query.get_or_404(grupo_id)

    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('reports.index'))

    buf = ReporteService.notas_grupo_excel(grupo)
    filename = f'notas_{grupo.codigo}.xlsx'
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, download_name=filename
    )


@reports_bp.route('/grupo/<int:grupo_id>/asistencia-excel')
@login_required
@profesor_or_admin
def asistencia_excel(grupo_id):
    """Excel con asistencia del grupo."""
    grupo = Grupo.query.get_or_404(grupo_id)

    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('reports.index'))

    buf = ReporteService.asistencia_grupo_excel(grupo)
    filename = f'asistencia_{grupo.codigo}.xlsx'
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, download_name=filename
    )
