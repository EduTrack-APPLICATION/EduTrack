"""
Rutas de Notas.
Soporta dos modos: individual (uno a uno) y grupal (toda la lista a la vez).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db, csrf
from app.models import Nota, Evaluacion, Estudiante, Grupo
from app.utils.decorators import profesor_or_admin

grades_bp = Blueprint('grades', __name__)


def _verificar_acceso_evaluacion(ev):
    """Retorna True si el usuario actual puede modificar la evaluación."""
    if current_user.is_admin():
        return True
    if current_user.is_profesor() and current_user.profesor:
        return ev.profesor_id == current_user.profesor.id
    return False


@grades_bp.route('/evaluacion/<int:evaluacion_id>', methods=['GET'])
@login_required
@profesor_or_admin
def calificar(evaluacion_id):
    """
    Vista principal de calificación.
    Muestra toda la lista del grupo con campo de nota por estudiante (modo grupal).
    """
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)

    if not _verificar_acceso_evaluacion(evaluacion):
        flash('Sin permisos para esta evaluación.', 'danger')
        return redirect(url_for('evaluations.listar'))

    grupo = evaluacion.grupo
    estudiantes = list(grupo.estudiantes.order_by('apellido', 'nombre'))

    # Cargar notas existentes
    notas_dict = {
        n.estudiante_id: n
        for n in Nota.query.filter_by(evaluacion_id=evaluacion_id).all()
    }

    # Preparar lista combinada
    items = []
    for est in estudiantes:
        nota = notas_dict.get(est.id)
        items.append({
            'estudiante': est,
            'nota_id': nota.id if nota else None,
            'puntaje': nota.puntaje if nota else None,
            'observaciones': nota.observaciones if nota else '',
        })

    # Stats
    notas_registradas = sum(1 for i in items if i['puntaje'] is not None)
    promedio = (sum(i['puntaje'] for i in items if i['puntaje'] is not None) /
                notas_registradas) if notas_registradas > 0 else 0

    return render_template(
        'grades/calificar.html',
        evaluacion=evaluacion,
        grupo=grupo,
        items=items,
        total_estudiantes=len(estudiantes),
        notas_registradas=notas_registradas,
        promedio=round(promedio, 2),
    )


@grades_bp.route('/evaluacion/<int:evaluacion_id>/guardar', methods=['POST'])
@login_required
@profesor_or_admin
def guardar_masivo(evaluacion_id):
    """Guarda múltiples notas al mismo tiempo (modo grupal)."""
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)

    if not _verificar_acceso_evaluacion(evaluacion):
        flash('Sin permisos.', 'danger')
        return redirect(url_for('evaluations.listar'))

    creadas = 0
    actualizadas = 0
    errores = 0

    for est in evaluacion.grupo.estudiantes:
        key = f'puntaje_{est.id}'
        obs_key = f'obs_{est.id}'

        if key not in request.form:
            continue

        valor = request.form.get(key, '').strip()
        observaciones = request.form.get(obs_key, '').strip() or None

        # Si está vacío, opcionalmente eliminar la nota existente
        if not valor:
            existente = Nota.query.filter_by(
                estudiante_id=est.id, evaluacion_id=evaluacion_id).first()
            if existente:
                db.session.delete(existente)
            continue

        try:
            puntaje = float(valor)
            if puntaje < 0 or puntaje > evaluacion.puntaje_maximo:
                errores += 1
                continue
        except ValueError:
            errores += 1
            continue

        nota = Nota.query.filter_by(
            estudiante_id=est.id, evaluacion_id=evaluacion_id).first()

        if nota:
            nota.puntaje = puntaje
            nota.observaciones = observaciones
            actualizadas += 1
        else:
            nota = Nota(
                estudiante_id=est.id,
                evaluacion_id=evaluacion_id,
                puntaje=puntaje,
                observaciones=observaciones,
            )
            db.session.add(nota)
            creadas += 1

    db.session.commit()

    mensaje = f'✓ {creadas} nota(s) registrada(s), {actualizadas} actualizada(s).'
    if errores > 0:
        mensaje += f' ⚠ {errores} con error (puntaje inválido).'
        flash(mensaje, 'warning')
    else:
        flash(mensaje, 'success')

    return redirect(url_for('grades.calificar', evaluacion_id=evaluacion_id))


@grades_bp.route('/api/nota/<int:evaluacion_id>/<int:estudiante_id>', methods=['POST'])
@login_required
@profesor_or_admin
@csrf.exempt  # API endpoint protegido por sesión
def api_guardar_nota(evaluacion_id, estudiante_id):
    """Endpoint AJAX para auto-guardado nota a nota (modo individual rápido)."""
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)

    if not _verificar_acceso_evaluacion(evaluacion):
        return jsonify({'error': 'Sin permisos'}), 403

    data = request.get_json() or {}
    puntaje_str = str(data.get('puntaje', '')).strip()
    observaciones = data.get('observaciones', '').strip() or None

    # Si está vacío, eliminar nota
    if not puntaje_str:
        existente = Nota.query.filter_by(
            estudiante_id=estudiante_id, evaluacion_id=evaluacion_id).first()
        if existente:
            db.session.delete(existente)
            db.session.commit()
        return jsonify({'success': True, 'eliminada': True})

    try:
        puntaje = float(puntaje_str)
        if puntaje < 0 or puntaje > evaluacion.puntaje_maximo:
            return jsonify({
                'error': f'El puntaje debe estar entre 0 y {evaluacion.puntaje_maximo}'
            }), 400
    except ValueError:
        return jsonify({'error': 'Puntaje inválido'}), 400

    nota = Nota.query.filter_by(
        estudiante_id=estudiante_id, evaluacion_id=evaluacion_id).first()

    if nota:
        nota.puntaje = puntaje
        nota.observaciones = observaciones
    else:
        nota = Nota(
            estudiante_id=estudiante_id,
            evaluacion_id=evaluacion_id,
            puntaje=puntaje,
            observaciones=observaciones,
        )
        db.session.add(nota)

    db.session.commit()

    porcentaje = (puntaje / evaluacion.puntaje_maximo) * 100
    return jsonify({
        'success': True,
        'puntaje': puntaje,
        'porcentaje': round(porcentaje, 1),
    })
