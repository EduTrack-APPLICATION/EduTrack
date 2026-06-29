"""
CRUD de Profesores (solo admin).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Usuario, Profesor, Materia, RolEnum
from app.utils.forms import ProfesorForm
from app.utils.decorators import admin_required

teachers_bp = Blueprint('teachers', __name__)


@teachers_bp.route('/')
@login_required
@admin_required
def listar():
    page = request.args.get('page', 1, type=int)
    buscar = request.args.get('q', '', type=str).strip()

    query = Profesor.query
    if buscar:
        like = f'%{buscar}%'
        query = query.filter(db.or_(
            Profesor.nombre.ilike(like),
            Profesor.apellido.ilike(like),
            Profesor.cedula.ilike(like),
            Profesor.especialidad.ilike(like),
        ))

    profesores = query.order_by(Profesor.apellido, Profesor.nombre).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('teachers/listar.html', profesores=profesores, buscar=buscar)


@teachers_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    form = ProfesorForm()
    if form.validate_on_submit():
        # Si no se especificó username, usar la cédula
        username = (form.username.data or '').strip() or form.cedula.data.strip()

        # Validar unicidad
        if Usuario.query.filter_by(username=username).first():
            flash(f'Ya existe un usuario con el nombre "{username}".', 'danger')
        elif Usuario.query.filter_by(email=form.email.data).first():
            flash('Ya existe un usuario con ese correo.', 'danger')
        elif Profesor.query.filter_by(cedula=form.cedula.data).first():
            flash('Ya existe un profesor con esa cédula.', 'danger')
        elif not form.password.data:
            flash('Debes establecer una contraseña inicial.', 'danger')
        else:
            usuario = Usuario(
                username=username,
                email=form.email.data,
                nombre_completo=f'{form.nombre.data} {form.apellido.data}',
                rol=RolEnum.PROFESOR.value,
                activo=form.activo.data,
            )
            usuario.set_password(form.password.data)
            db.session.add(usuario)

            try:
                db.session.flush()

                profesor = Profesor(
                    usuario_id=usuario.id,
                    cedula=form.cedula.data,
                    nombre=form.nombre.data,
                    apellido=form.apellido.data,
                    telefono=form.telefono.data,
                    direccion=form.direccion.data,
                    especialidad=form.especialidad.data,
                    titulo=form.titulo.data,
                    activo=form.activo.data,
                )
                db.session.add(profesor)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Ya existe un usuario o profesor con esos datos (usuario, correo o cédula).',
                      'danger')
                return render_template('teachers/form.html', form=form, titulo='Nuevo profesor')
            flash(
                f'Profesor {profesor.nombre_completo} creado correctamente. '
                f'Credenciales: usuario "{username}" · '
                f'la contraseña inicial que definiste. '
                f'Comparte estas credenciales con el profesor.',
                'success'
            )
            return redirect(url_for('teachers.detalle', id=profesor.id))

    return render_template('teachers/form.html', form=form, titulo='Nuevo profesor')


@teachers_bp.route('/<int:id>')
@login_required
@admin_required
def detalle(id):
    profesor = Profesor.query.get_or_404(id)
    materias = Materia.query.filter_by(activa=True).all()
    materias_asignadas_ids = [m.id for m in profesor.materias]
    return render_template(
        'teachers/detalle.html',
        profesor=profesor,
        materias=materias,
        materias_asignadas_ids=materias_asignadas_ids,
    )


@teachers_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    profesor = Profesor.query.get_or_404(id)
    form = ProfesorForm(obj=profesor)
    form.username.data = profesor.usuario.username
    form.email.data = profesor.usuario.email

    if request.method == 'POST' and form.validate_on_submit():
        # Verificar duplicados (excluyendo el actual)
        otro_user = Usuario.query.filter(
            Usuario.username == form.username.data,
            Usuario.id != profesor.usuario_id
        ).first()
        otro_email = Usuario.query.filter(
            Usuario.email == form.email.data,
            Usuario.id != profesor.usuario_id
        ).first()

        if otro_user:
            flash('Ya existe otro usuario con ese nombre.', 'danger')
        elif otro_email:
            flash('Ya existe otro usuario con ese correo.', 'danger')
        else:
            profesor.cedula = form.cedula.data
            profesor.nombre = form.nombre.data
            profesor.apellido = form.apellido.data
            profesor.telefono = form.telefono.data
            profesor.direccion = form.direccion.data
            profesor.especialidad = form.especialidad.data
            profesor.titulo = form.titulo.data
            profesor.activo = form.activo.data

            profesor.usuario.username = form.username.data
            profesor.usuario.email = form.email.data
            profesor.usuario.nombre_completo = f'{form.nombre.data} {form.apellido.data}'
            profesor.usuario.activo = form.activo.data

            if form.password.data:
                profesor.usuario.set_password(form.password.data)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Ya existe un usuario o profesor con esos datos (usuario, correo o cédula).',
                      'danger')
                return render_template('teachers/form.html', form=form,
                                       titulo=f'Editar: {profesor.nombre_completo}',
                                       profesor=profesor)
            flash('Profesor actualizado correctamente.', 'success')
            return redirect(url_for('teachers.detalle', id=id))

    return render_template('teachers/form.html', form=form,
                           titulo=f'Editar: {profesor.nombre_completo}',
                           profesor=profesor)


@teachers_bp.route('/<int:id>/asignar-materias', methods=['POST'])
@login_required
@admin_required
def asignar_materias(id):
    profesor = Profesor.query.get_or_404(id)
    materia_ids = request.form.getlist('materia_ids', type=int)

    # Limpiar y reasignar
    profesor.materias = Materia.query.filter(Materia.id.in_(materia_ids)).all() \
        if materia_ids else []
    db.session.commit()
    flash('Materias asignadas correctamente.', 'success')
    return redirect(url_for('teachers.detalle', id=id))


@teachers_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    profesor = Profesor.query.get_or_404(id)
    if profesor.grupos.count() > 0:
        flash('No se puede eliminar: el profesor tiene grupos asignados.', 'danger')
        return redirect(url_for('teachers.detalle', id=id))

    nombre = profesor.nombre_completo
    db.session.delete(profesor.usuario)  # cascade elimina al profesor
    db.session.commit()
    flash(f'Profesor {nombre} eliminado.', 'success')
    return redirect(url_for('teachers.listar'))
