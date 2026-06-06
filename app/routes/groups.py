"""
CRUD de Grupos.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Grupo, Materia, Profesor, Estudiante
from app.utils.forms import GrupoForm
from app.utils.decorators import admin_required, profesor_or_admin
from app.services.calculo_service import CalculoService

groups_bp = Blueprint('groups', __name__)


def _llenar_choices(form):
    form.materia_id.choices = [(m.id, f'{m.codigo} — {m.nombre}')
                                for m in Materia.query.filter_by(activa=True).order_by(Materia.codigo)]
    form.profesor_id.choices = [(p.id, p.nombre_completo)
                                 for p in Profesor.query.filter_by(activo=True).order_by(Profesor.apellido)]


@groups_bp.route('/')
@login_required
@profesor_or_admin
def listar():
    page = request.args.get('page', 1, type=int)
    buscar = request.args.get('q', '', type=str).strip()
    materia_id = request.args.get('materia', type=int)
    query = Grupo.query

    # Profesor solo ve sus grupos
    if current_user.is_profesor() and current_user.profesor:
        query = query.filter_by(profesor_id=current_user.profesor.id)

    if materia_id:
        query = query.filter_by(materia_id=materia_id)

    if buscar:
        like = f'%{buscar}%'
        query = query.filter(db.or_(
            Grupo.codigo.ilike(like), Grupo.nombre.ilike(like)
        ))

    grupos = query.order_by(Grupo.codigo).paginate(page=page, per_page=20, error_out=False)
    return render_template('groups/listar.html', grupos=grupos, buscar=buscar)


@groups_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    form = GrupoForm()
    _llenar_choices(form)

    # Si no hay materias o profesores activos, redirigir con aviso
    if not form.materia_id.choices:
        flash('No hay materias activas. Crea al menos una materia antes de crear grupos.', 'warning')
        return redirect(url_for('subjects.listar'))
    if not form.profesor_id.choices:
        flash('No hay profesores activos. Registra al menos un profesor antes de crear grupos.', 'warning')
        return redirect(url_for('teachers.listar'))

    # Preseleccionar materia o profesor desde la URL (atajos desde otras pantallas)
    if request.method == 'GET':
        materia_id = request.args.get('materia_id', type=int)
        profesor_id = request.args.get('profesor_id', type=int)
        if materia_id and materia_id in [c[0] for c in form.materia_id.choices]:
            form.materia_id.data = materia_id
        if profesor_id and profesor_id in [c[0] for c in form.profesor_id.choices]:
            form.profesor_id.data = profesor_id

    if form.validate_on_submit():
        if Grupo.query.filter_by(codigo=form.codigo.data).first():
            flash('Ya existe un grupo con ese código.', 'danger')
        else:
            g = Grupo()
            form.populate_obj(g)
            db.session.add(g)
            db.session.commit()
            flash(f'Grupo {g.codigo} creado. Ahora matricula estudiantes para empezar a usarlo.',
                  'success')
            return redirect(url_for('groups.detalle', id=g.id))
    return render_template('groups/form.html', form=form, titulo='Nuevo grupo')


@groups_bp.route('/<int:id>')
@login_required
@profesor_or_admin
def detalle(id):
    grupo = Grupo.query.get_or_404(id)

    # Verificar permisos: profesor solo accede a sus grupos
    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('No tienes permiso para acceder a este grupo.', 'danger')
        return redirect(url_for('groups.listar'))

    estudiantes_info = []
    for est in grupo.estudiantes.order_by('apellido'):
        calc = CalculoService.nota_final_estudiante(est.id, grupo.id)
        asist = CalculoService.porcentaje_asistencia(est.id, grupo.id)
        estado_key, estado_label, estado_color = CalculoService.estado_academico(
            calc['nota_final'], calc['porcentaje_acumulado'])
        estudiantes_info.append({
            'estudiante': est, 'calc': calc, 'asistencia': asist,
            'estado_label': estado_label, 'estado_color': estado_color,
        })

    # IDs ya matriculados (para modal de matrícula)
    matriculados_ids = [e.id for e in grupo.estudiantes]
    disponibles = Estudiante.query.filter(
        ~Estudiante.id.in_(matriculados_ids)
    ).filter_by(estado='activo').order_by(Estudiante.apellido).all() if matriculados_ids else \
        Estudiante.query.filter_by(estado='activo').order_by(Estudiante.apellido).all()

    return render_template('groups/detalle.html', grupo=grupo,
                           estudiantes_info=estudiantes_info,
                           disponibles=disponibles)


@groups_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    grupo = Grupo.query.get_or_404(id)
    form = GrupoForm(obj=grupo)
    _llenar_choices(form)
    if form.validate_on_submit():
        otro = Grupo.query.filter(Grupo.codigo == form.codigo.data, Grupo.id != id).first()
        if otro:
            flash('Ya existe otro grupo con ese código.', 'danger')
        else:
            form.populate_obj(grupo)
            db.session.commit()
            flash('Grupo actualizado.', 'success')
            return redirect(url_for('groups.detalle', id=id))
    return render_template('groups/form.html', form=form,
                           titulo=f'Editar: {grupo.codigo}', grupo=grupo)


@groups_bp.route('/<int:id>/matricular', methods=['POST'])
@login_required
@profesor_or_admin
def matricular(id):
    grupo = Grupo.query.get_or_404(id)
    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('Sin permisos para este grupo.', 'danger')
        return redirect(url_for('groups.detalle', id=id))

    estudiante_ids = request.form.getlist('estudiante_ids', type=int)
    matriculados = 0
    for eid in estudiante_ids:
        est = Estudiante.query.get(eid)
        if est and est not in grupo.estudiantes:
            grupo.estudiantes.append(est)
            matriculados += 1
    db.session.commit()
    flash(f'{matriculados} estudiante(s) matriculado(s).', 'success')
    return redirect(url_for('groups.detalle', id=id))


@groups_bp.route('/<int:id>/desmatricular/<int:estudiante_id>', methods=['POST'])
@login_required
@profesor_or_admin
def desmatricular(id, estudiante_id):
    grupo = Grupo.query.get_or_404(id)
    if current_user.is_profesor() and current_user.profesor and \
       grupo.profesor_id != current_user.profesor.id:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('groups.detalle', id=id))

    est = Estudiante.query.get_or_404(estudiante_id)
    if est in grupo.estudiantes:
        grupo.estudiantes.remove(est)
        db.session.commit()
        flash(f'{est.nombre_completo} desmatriculado.', 'info')
    return redirect(url_for('groups.detalle', id=id))


@groups_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    grupo = Grupo.query.get_or_404(id)
    cod = grupo.codigo
    db.session.delete(grupo)
    db.session.commit()
    flash(f'Grupo {cod} eliminado.', 'success')
    return redirect(url_for('groups.listar'))
