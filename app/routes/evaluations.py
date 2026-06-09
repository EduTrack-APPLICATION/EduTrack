"""
CRUD de Evaluaciones.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Evaluacion, Grupo, Materia
from app.utils.forms import EvaluacionForm
from app.utils.decorators import profesor_or_admin

evaluations_bp = Blueprint('evaluations', __name__)


def _llenar_choices(form, profesor_id=None):
    query = Grupo.query.filter_by(activo=True)
    if profesor_id:
        query = query.filter_by(profesor_id=profesor_id)
    form.grupo_id.choices = [
        (g.id, f'{g.codigo} — {g.materia.nombre}')
        for g in query.order_by(Grupo.codigo).all()
    ]


@evaluations_bp.route('/')
@login_required
@profesor_or_admin
def listar():
    page = request.args.get('page', 1, type=int)
    grupo_id = request.args.get('grupo_id', type=int)
    tipo = request.args.get('tipo', '', type=str)

    query = Evaluacion.query
    if current_user.is_profesor() and current_user.profesor:
        query = query.filter_by(profesor_id=current_user.profesor.id)

    if grupo_id:
        query = query.filter_by(grupo_id=grupo_id)
    if tipo:
        query = query.filter_by(tipo=tipo)

    evaluaciones = query.order_by(Evaluacion.fecha.desc()).paginate(
        page=page, per_page=20, error_out=False)

    grupos_q = Grupo.query
    if current_user.is_profesor() and current_user.profesor:
        grupos_q = grupos_q.filter_by(profesor_id=current_user.profesor.id)
    grupos = grupos_q.order_by(Grupo.codigo).all()

    return render_template('evaluations/listar.html', evaluaciones=evaluaciones,
                           grupos=grupos, grupo_id=grupo_id, tipo=tipo)


@evaluations_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@profesor_or_admin
def crear():
    form = EvaluacionForm()
    profesor_id = current_user.profesor.id if current_user.is_profesor() and current_user.profesor else None
    _llenar_choices(form, profesor_id)

    if form.validate_on_submit():
        grupo = Grupo.query.get(form.grupo_id.data)
        if not grupo:
            flash('Grupo no válido.', 'danger')
        else:
            ev = Evaluacion(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                tipo=form.tipo.data,
                fecha=form.fecha.data,
                puntaje_maximo=form.puntaje_maximo.data,
                porcentaje=form.porcentaje.data,
                materia_id=grupo.materia_id,
                grupo_id=grupo.id,
                profesor_id=grupo.profesor_id,
            )
            db.session.add(ev)
            db.session.commit()
            flash(f'Evaluación "{ev.nombre}" creada.', 'success')
            return redirect(url_for('grades.calificar', evaluacion_id=ev.id))

    return render_template('evaluations/form.html', form=form, titulo='Nueva evaluación')


@evaluations_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@profesor_or_admin
def editar(id):
    ev = Evaluacion.query.get_or_404(id)

    # Permisos
    if current_user.is_profesor() and current_user.profesor and \
       ev.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('evaluations.listar'))

    form = EvaluacionForm(obj=ev)
    profesor_id = current_user.profesor.id if current_user.is_profesor() and current_user.profesor else None
    _llenar_choices(form, profesor_id)

    if form.validate_on_submit():
        grupo = Grupo.query.get(form.grupo_id.data)
        ev.nombre = form.nombre.data
        ev.descripcion = form.descripcion.data
        ev.tipo = form.tipo.data
        ev.fecha = form.fecha.data
        ev.puntaje_maximo = form.puntaje_maximo.data
        ev.porcentaje = form.porcentaje.data
        ev.grupo_id = grupo.id
        ev.materia_id = grupo.materia_id
        db.session.commit()
        flash('Evaluación actualizada.', 'success')
        return redirect(url_for('evaluations.listar'))

    return render_template('evaluations/form.html', form=form,
                           titulo=f'Editar: {ev.nombre}', evaluacion=ev)


@evaluations_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@profesor_or_admin
def eliminar(id):
    ev = Evaluacion.query.get_or_404(id)
    if current_user.is_profesor() and current_user.profesor and \
       ev.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('evaluations.listar'))
    nombre = ev.nombre
    db.session.delete(ev)
    db.session.commit()
    flash(f'Evaluación "{nombre}" eliminada.', 'success')
    return redirect(url_for('evaluations.listar'))


