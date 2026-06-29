"""
CRUD de Estudiantes.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Estudiante, Grupo, EstadoEstudianteEnum
from app.utils.forms import EstudianteForm
from app.utils.decorators import profesor_or_admin, admin_required
from app.services.calculo_service import CalculoService

students_bp = Blueprint('students', __name__)


@students_bp.route('/')
@login_required
@profesor_or_admin
def listar():
    page = request.args.get('page', 1, type=int)
    buscar = request.args.get('q', '', type=str).strip()
    grupo_id = request.args.get('grupo_id', type=int)
    estado = request.args.get('estado', '', type=str)

    query = Estudiante.query.filter(Estudiante.eliminado_en.is_(None))

    if buscar:
        like = f'%{buscar}%'
        query = query.filter(or_(
            Estudiante.nombre.ilike(like),
            Estudiante.apellido.ilike(like),
            Estudiante.codigo.ilike(like),
            Estudiante.cedula.ilike(like),
            Estudiante.email.ilike(like),
        ))

    if grupo_id:
        query = query.filter(Estudiante.grupos.any(Grupo.id == grupo_id))

    if estado:
        query = query.filter(Estudiante.estado == estado)

    estudiantes = query.order_by(Estudiante.apellido, Estudiante.nombre).paginate(
        page=page, per_page=20, error_out=False
    )

    grupos = Grupo.query.filter_by(activo=True).order_by(Grupo.codigo).all()

    return render_template(
        'students/listar.html',
        estudiantes=estudiantes,
        grupos=grupos,
        buscar=buscar,
        grupo_id=grupo_id,
        estado=estado,
    )


@students_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@profesor_or_admin
def crear():
    form = EstudianteForm()
    if form.validate_on_submit():
        # Validar unicidad
        if Estudiante.query.filter_by(codigo=form.codigo.data).first():
            flash('Ya existe un estudiante con ese código.', 'danger')
        elif form.cedula.data and Estudiante.query.filter_by(cedula=form.cedula.data).first():
            flash('Ya existe un estudiante con esa cédula.', 'danger')
        elif form.email.data and Estudiante.query.filter_by(email=form.email.data).first():
            flash('Ya existe un estudiante con ese correo electrónico.', 'danger')
        else:
            est = Estudiante(
                codigo=form.codigo.data, cedula=form.cedula.data,
                nombre=form.nombre.data, apellido=form.apellido.data,
                email=form.email.data, telefono=form.telefono.data,
                fecha_nacimiento=form.fecha_nacimiento.data,
                direccion=form.direccion.data, seccion=form.seccion.data,
                encargado=form.encargado.data,
                telefono_encargado=form.telefono_encargado.data,
                estado=form.estado.data,
            )
            db.session.add(est)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Ya existe un estudiante con ese código, cédula o correo electrónico.',
                      'danger')
                return render_template('students/form.html', form=form, titulo='Nuevo estudiante')

            # Generar cuenta del portal automáticamente
            try:
                from app.utils.portal_helpers import generar_cuenta_estudiante
                cuenta = generar_cuenta_estudiante(est)
                if cuenta:
                    flash(
                        f'Estudiante {est.nombre_completo} creado. '
                        f'Cuenta del portal: usuario "{cuenta["username"]}" · '
                        f'contraseña temporal "{cuenta["password"]}" '
                        f'(deberá cambiarla al primer login).',
                        'success'
                    )
                else:
                    flash(f'Estudiante {est.nombre_completo} creado correctamente.', 'success')
            except Exception as e:
                # Si falla la cuenta, no romper la creación del estudiante
                flash(f'Estudiante {est.nombre_completo} creado, pero falló la generación '
                      f'de su cuenta del portal. Puedes generarla desde el detalle. '
                      f'({type(e).__name__})', 'warning')

            return redirect(url_for('students.detalle', id=est.id))

    return render_template('students/form.html', form=form, titulo='Nuevo estudiante')


@students_bp.route('/<int:id>')
@login_required
@profesor_or_admin
def detalle(id):
    estudiante = Estudiante.query.get_or_404(id)

    # Resumen por grupo
    grupos_info = []
    for grupo in estudiante.grupos:
        calc = CalculoService.nota_final_estudiante(estudiante.id, grupo.id)
        asist = CalculoService.porcentaje_asistencia(estudiante.id, grupo.id)
        estado_key, estado_label, estado_color = CalculoService.estado_academico(
            calc['nota_final'], calc['porcentaje_acumulado'])
        grupos_info.append({
            'grupo': grupo, 'calc': calc, 'asistencia': asist,
            'estado_label': estado_label, 'estado_color': estado_color,
        })

    alertas = CalculoService.alertas_estudiante(estudiante.id)

    # ¿Ya tiene cuenta del portal?
    from app.utils.portal_helpers import tiene_cuenta_portal
    tiene_cuenta = tiene_cuenta_portal(estudiante)

    return render_template(
        'students/detalle.html',
        estudiante=estudiante,
        grupos_info=grupos_info,
        alertas=alertas,
        tiene_cuenta_portal=tiene_cuenta,
    )


@students_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@profesor_or_admin
def editar(id):
    estudiante = Estudiante.query.get_or_404(id)
    form = EstudianteForm(obj=estudiante)

    if form.validate_on_submit():
        # Verificar duplicados (excluyendo el actual)
        otro_codigo = Estudiante.query.filter(
            Estudiante.codigo == form.codigo.data,
            Estudiante.id != id
        ).first()
        otro_cedula = form.cedula.data and Estudiante.query.filter(
            Estudiante.cedula == form.cedula.data,
            Estudiante.id != id
        ).first()
        otro_email = form.email.data and Estudiante.query.filter(
            Estudiante.email == form.email.data,
            Estudiante.id != id
        ).first()
        if otro_codigo:
            flash('Ya existe otro estudiante con ese código.', 'danger')
        elif otro_cedula:
            flash('Ya existe otro estudiante con esa cédula.', 'danger')
        elif otro_email:
            flash('Ya existe otro estudiante con ese correo electrónico.', 'danger')
        else:
            form.populate_obj(estudiante)
            db.session.commit()
            flash('Estudiante actualizado correctamente.', 'success')
            return redirect(url_for('students.detalle', id=id))

    return render_template('students/form.html', form=form,
                           titulo=f'Editar: {estudiante.nombre_completo}',
                           estudiante=estudiante)


@students_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    """Soft delete — mueve a papelera."""
    estudiante = Estudiante.query.get_or_404(id)
    nombre = estudiante.nombre_completo
    estudiante.eliminado_en = datetime.utcnow()
    db.session.commit()
    flash(f'{nombre} movido a la papelera. Puedes restaurarlo en los próximos 30 días.',
          'success')
    return redirect(url_for('students.listar'))


@students_bp.route('/papelera')
@login_required
@admin_required
def papelera():
    """Lista estudiantes en la papelera (últimos 30 días)."""
    desde = datetime.utcnow() - timedelta(days=30)
    estudiantes = Estudiante.query.filter(
        Estudiante.eliminado_en.isnot(None),
        Estudiante.eliminado_en >= desde
    ).order_by(Estudiante.eliminado_en.desc()).all()
    return render_template('students/papelera.html', estudiantes=estudiantes)


@students_bp.route('/<int:id>/restaurar', methods=['POST'])
@login_required
@admin_required
def restaurar(id):
    """Restaura un estudiante de la papelera."""
    estudiante = Estudiante.query.get_or_404(id)
    if not estudiante.eliminado_en:
        flash('Este estudiante no está en la papelera.', 'warning')
    else:
        estudiante.eliminado_en = None
        db.session.commit()
        flash(f'{estudiante.nombre_completo} restaurado correctamente.', 'success')
    return redirect(url_for('students.papelera'))


@students_bp.route('/<int:id>/eliminar-definitivo', methods=['POST'])
@login_required
@admin_required
def eliminar_definitivo(id):
    """Borrado real — solo desde la papelera."""
    estudiante = Estudiante.query.get_or_404(id)
    if not estudiante.eliminado_en:
        flash('Solo se pueden eliminar definitivamente estudiantes de la papelera.',
              'warning')
        return redirect(url_for('students.listar'))
    nombre = estudiante.nombre_completo
    db.session.delete(estudiante)
    db.session.commit()
    flash(f'{nombre} eliminado definitivamente.', 'info')
    return redirect(url_for('students.papelera'))


@students_bp.route('/api/buscar')
@login_required
@profesor_or_admin
def api_buscar():
    """Endpoint JSON para autocompletar."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    like = f'%{q}%'
    estudiantes = Estudiante.query.filter(
        Estudiante.eliminado_en.is_(None),
        or_(
            Estudiante.nombre.ilike(like),
            Estudiante.apellido.ilike(like),
            Estudiante.codigo.ilike(like),
        )
    ).limit(15).all()
    return jsonify([{
        'id': e.id, 'codigo': e.codigo,
        'nombre': e.nombre_completo, 'email': e.email,
    } for e in estudiantes])


# ============================================================
# Importación masiva desde Excel/CSV
# ============================================================

@students_bp.route('/importar', methods=['GET'])
@login_required
@admin_required
def importar():
    """Página principal de importación."""
    return render_template('students/importar.html')


@students_bp.route('/importar/plantilla')
@login_required
@admin_required
def importar_plantilla():
    """Descarga la plantilla Excel para llenar."""
    from flask import send_file
    from app.services.importador_service import ImportadorEstudiantes
    buf = ImportadorEstudiantes.generar_plantilla()
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='plantilla_estudiantes_edutrack.xlsx',
    )


@students_bp.route('/importar/preview', methods=['POST'])
@login_required
@admin_required
def importar_preview():
    """Recibe el archivo, valida y muestra vista previa."""
    from app.services.importador_service import ImportadorEstudiantes
    import json
    from datetime import date, datetime

    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        flash('No se recibió ningún archivo.', 'danger')
        return redirect(url_for('students.importar'))

    filas, error = ImportadorEstudiantes.parsear(archivo)
    if error:
        flash(error, 'danger')
        return redirect(url_for('students.importar'))

    if not filas:
        flash('El archivo no contiene filas con datos.', 'warning')
        return redirect(url_for('students.importar'))

    resultados = ImportadorEstudiantes.validar(filas)

    # Contadores para el resumen
    total = len(resultados)
    importables = sum(1 for r in resultados if r['valido'] and not r['existe'])
    duplicados = sum(1 for r in resultados if r['valido'] and r['existe'])
    con_errores = sum(1 for r in resultados if not r['valido'])

    # Serializar resultados para que el form de confirmación los reciba
    def _serializar_datos(d):
        out = {}
        for k, v in d.items():
            if isinstance(v, datetime):
                out[k] = v.date().isoformat()
            elif isinstance(v, date):
                out[k] = v.isoformat()
            else:
                out[k] = v
        return out

    # Serializar datos_raw también (pueden tener datetime)
    def _serializar_raw(d):
        out = {}
        for k, v in d.items():
            if isinstance(v, (date, datetime)):
                out[k] = v.isoformat()
            else:
                out[k] = v
        return out

    payload = [{
        'fila': r['fila'],
        'datos': _serializar_datos(r['datos']),
        'datos_raw': _serializar_raw(r['datos_raw']),
        'errores': r['errores'],
        'advertencias': r['advertencias'],
        'valido': r['valido'],
        'existe': r['existe'],
    } for r in resultados]

    return render_template(
        'students/importar_preview.html',
        resultados=resultados,
        total=total,
        importables=importables,
        duplicados=duplicados,
        con_errores=con_errores,
        payload_json=json.dumps(payload, ensure_ascii=False),
        nombre_archivo=archivo.filename,
    )


@students_bp.route('/importar/confirmar', methods=['POST'])
@login_required
@admin_required
def importar_confirmar():
    """Procesa la importación real (después de la vista previa)."""
    from app.services.importador_service import ImportadorEstudiantes
    from datetime import date as _date
    import json

    payload_str = request.form.get('payload')
    if not payload_str:
        flash('Sesión de importación expirada. Sube el archivo de nuevo.', 'danger')
        return redirect(url_for('students.importar'))

    try:
        payload = json.loads(payload_str)
    except Exception:
        flash('No se pudo procesar la importación. Sube el archivo de nuevo.', 'danger')
        return redirect(url_for('students.importar'))

    # Re-hidratar las fechas
    for r in payload:
        datos = r.get('datos', {})
        if datos.get('fecha_nacimiento'):
            try:
                datos['fecha_nacimiento'] = _date.fromisoformat(datos['fecha_nacimiento'])
            except (ValueError, TypeError):
                datos['fecha_nacimiento'] = None

    try:
        resumen = ImportadorEstudiantes.importar(payload)
    except Exception as e:
        flash(f'Error al importar: {e}', 'danger')
        return redirect(url_for('students.importar'))

    # Generar cuentas del portal para los recién importados
    try:
        from app.utils.portal_helpers import generar_cuenta_estudiante
        estudiantes_creados = resumen.get('estudiantes_creados') if isinstance(resumen, dict) else None
        if estudiantes_creados:
            creadas = 0
            for est in estudiantes_creados:
                if generar_cuenta_estudiante(est, commit=False):
                    creadas += 1
            db.session.commit()
            if creadas:
                flash(f'Se generaron {creadas} cuenta(s) del portal automáticamente. '
                      f'Para ver las credenciales, ejecuta `python crear_cuentas_estudiantes.py --reset <id>` '
                      f'o entra al detalle del estudiante.', 'info')
    except Exception:
        # Si falla, no romper el import
        pass

    return render_template(
        'students/importar_resultado.html',
        resumen=resumen,
    )


# ============================================================
# Cuenta del portal del estudiante
# ============================================================

@students_bp.route('/<int:id>/cuenta-portal/generar', methods=['POST'])
@login_required
@admin_required
def generar_cuenta_portal(id):
    """Genera (o resetea) la cuenta del portal para el estudiante."""
    from app.utils.portal_helpers import generar_cuenta_estudiante

    est = Estudiante.query.get_or_404(id)
    if est.eliminado_en:
        flash('No se puede generar cuenta para un estudiante en la papelera.', 'warning')
        return redirect(url_for('students.detalle', id=id))

    # ¿Reset si ya existe?
    reset = request.form.get('reset') == '1'

    cuenta = generar_cuenta_estudiante(est, reset=reset)
    if cuenta is None:
        flash(f'{est.nombre_completo} ya tiene cuenta del portal. '
              f'Usa "Resetear contraseña" si quieres generar una nueva.', 'info')
    else:
        accion = 'reseteada' if cuenta['reset'] else 'creada'
        flash(
            f'Cuenta del portal {accion} para {est.nombre_completo}. '
            f'Usuario: "{cuenta["username"]}" · '
            f'Contraseña temporal: "{cuenta["password"]}" '
            f'(deberá cambiarla al primer login).',
            'success'
        )
    return redirect(url_for('students.detalle', id=id))
