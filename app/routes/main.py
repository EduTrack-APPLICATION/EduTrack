"""Ruta principal y endpoint de búsqueda global."""
from flask import Blueprint, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@main_bp.route('/api/buscar-global')
@login_required
def buscar_global():
    """
    Endpoint JSON unificado: busca en estudiantes, profesores, materias y grupos
    a partir de una sola consulta. Útil para la búsqueda global Ctrl+K.
    """
    from app.models import Estudiante, Profesor, Materia, Grupo

    q = request.args.get('q', '', type=str).strip()
    if len(q) < 2:
        return jsonify({'resultados': [], 'total': 0})

    like = f'%{q}%'
    resultados = []

    # --- Estudiantes ---
    estudiantes = Estudiante.query.filter(or_(
        Estudiante.nombre.ilike(like),
        Estudiante.apellido.ilike(like),
        Estudiante.codigo.ilike(like),
        Estudiante.cedula.ilike(like),
        Estudiante.email.ilike(like),
    )).limit(8).all()
    for e in estudiantes:
        resultados.append({
            'tipo': 'estudiante',
            'tipo_label': 'Estudiante',
            'icono': 'bi-mortarboard',
            'color': 'primary',
            'titulo': e.nombre_completo,
            'subtitulo': (e.codigo or '—') + (' · ' + e.email if e.email else ''),
            'url': url_for('students.detalle', id=e.id),
            'id': e.id,
        })

    # --- Profesores (solo admin) ---
    if current_user.is_admin():
        profesores = Profesor.query.filter(or_(
            Profesor.nombre.ilike(like),
            Profesor.apellido.ilike(like),
            Profesor.cedula.ilike(like),
            Profesor.especialidad.ilike(like),
        )).limit(5).all()
        for p in profesores:
            resultados.append({
                'tipo': 'profesor',
                'tipo_label': 'Profesor',
                'icono': 'bi-person-badge',
                'color': 'success',
                'titulo': p.nombre_completo,
                'subtitulo': (p.especialidad or 'Profesor') +
                             (' · ' + p.email if p.email else ''),
                'url': url_for('teachers.detalle', id=p.id),
                'id': p.id,
            })

    # --- Materias ---
    materias = Materia.query.filter(or_(
        Materia.nombre.ilike(like),
        Materia.codigo.ilike(like),
    )).limit(5).all()
    for m in materias:
        resultados.append({
            'tipo': 'materia',
            'tipo_label': 'Materia',
            'icono': 'bi-book',
            'color': 'warning',
            'titulo': m.nombre,
            'subtitulo': f'{m.codigo} · {m.creditos} créditos · {m.grupos.count()} grupos',
            'url': url_for('subjects.editar', id=m.id) if current_user.is_admin()
                   else url_for('subjects.listar'),
            'id': m.id,
        })

    # --- Grupos ---
    grupos_query = Grupo.query.filter(or_(
        Grupo.codigo.ilike(like),
        Grupo.nombre.ilike(like),
    ))
    # Profesores solo ven sus propios grupos
    if current_user.is_profesor() and current_user.profesor:
        grupos_query = grupos_query.filter_by(profesor_id=current_user.profesor.id)
    grupos = grupos_query.limit(5).all()
    for g in grupos:
        resultados.append({
            'tipo': 'grupo',
            'tipo_label': 'Grupo',
            'icono': 'bi-people',
            'color': 'info',
            'titulo': f'{g.codigo} — {g.nombre}',
            'subtitulo': (g.materia.nombre if g.materia else '—') +
                         ' · ' + (g.profesor.nombre_completo if g.profesor else '—'),
            'url': url_for('groups.detalle', id=g.id),
            'id': g.id,
        })

    return jsonify({'resultados': resultados, 'total': len(resultados)})


@main_bp.route('/api/version')
@login_required
def api_version():
    """
    Endpoint para detectar cambios en la BD.
    Retorna un 'hash' (basado en el max timestamp de las tablas que cambian
    más seguido). Si el hash cambia, hay nuevos datos.
    """
    from app.models import Estudiante, Evaluacion, Nota, Asistencia, Grupo
    from sqlalchemy import func

    # Tomar el max timestamp de cada tabla relevante
    timestamps = []
    for model, field_name in [
        (Estudiante, 'fecha_creacion'),
        (Evaluacion, 'fecha_creacion'),
        (Grupo,      'fecha_creacion'),
        (Nota,       'fecha_actualizacion'),
        (Asistencia, 'fecha_actualizacion'),
    ]:
        field = getattr(model, field_name)
        result = db.session.query(func.max(field)).scalar()
        if result:
            timestamps.append(result.isoformat())

    # Combinar en un único hash simple
    import hashlib
    combined = '|'.join(sorted(timestamps))
    version = hashlib.md5(combined.encode()).hexdigest()[:12]

    return jsonify({
        'version': version,
        'timestamp': max(timestamps) if timestamps else None,
    })
