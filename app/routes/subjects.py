"""
CRUD de Materias.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Materia
from app.utils.forms import MateriaForm
from app.utils.decorators import admin_required, profesor_or_admin

subjects_bp = Blueprint('subjects', __name__)


@subjects_bp.route('/')
@login_required
@profesor_or_admin
def listar():
    page = request.args.get('page', 1, type=int)
    buscar = request.args.get('q', '', type=str).strip()
    query = Materia.query
    if buscar:
        like = f'%{buscar}%'
        query = query.filter(db.or_(
            Materia.nombre.ilike(like),
            Materia.codigo.ilike(like),
        ))
    materias = query.order_by(Materia.codigo).paginate(page=page, per_page=20, error_out=False)
    return render_template('subjects/listar.html', materias=materias, buscar=buscar)


@subjects_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    form = MateriaForm()
    if form.validate_on_submit():
        if Materia.query.filter_by(codigo=form.codigo.data).first():
            flash('Ya existe una materia con ese código.', 'danger')
        else:
            m = Materia()
            form.populate_obj(m)
            db.session.add(m)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Ya existe una materia con ese código.', 'danger')
                return render_template('subjects/form.html', form=form, titulo='Nueva materia')
            flash(
                f'Materia "{m.nombre}" creada. '
                f'Ahora crea un grupo para poder asignar evaluaciones y matricular estudiantes.',
                'success'
            )
            return redirect(url_for('groups.crear', materia_id=m.id))
    return render_template('subjects/form.html', form=form, titulo='Nueva materia')


@subjects_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    materia = Materia.query.get_or_404(id)
    form = MateriaForm(obj=materia)
    if form.validate_on_submit():
        otro = Materia.query.filter(Materia.codigo == form.codigo.data, Materia.id != id).first()
        if otro:
            flash('Ya existe otra materia con ese código.', 'danger')
        else:
            form.populate_obj(materia)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Ya existe otra materia con ese código.', 'danger')
                return render_template('subjects/form.html', form=form,
                                       titulo=f'Editar: {materia.nombre}', materia=materia)
            flash('Materia actualizada.', 'success')
            return redirect(url_for('subjects.listar'))
    return render_template('subjects/form.html', form=form,
                           titulo=f'Editar: {materia.nombre}', materia=materia)


@subjects_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    materia = Materia.query.get_or_404(id)
    if materia.grupos.count() > 0:
        flash('No se puede eliminar: la materia tiene grupos asociados.', 'danger')
    else:
        db.session.delete(materia)
        db.session.commit()
        flash(f'Materia {materia.nombre} eliminada.', 'success')
    return redirect(url_for('subjects.listar'))
