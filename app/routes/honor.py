"""
Cuadro de Honor — ranking de estudiantes por promedio
con generación de diplomas en PDF.
"""
from flask import Blueprint, render_template, request, send_file, abort
from flask_login import login_required, current_user

from app.models import Grupo, Materia, Estudiante
from app.services.calculo_service import CalculoService
from app.services.reporte_service import ReporteService

honor_bp = Blueprint('honor', __name__)


def _aplicar_filtros_profesor(grupos_qs):
    """Si el usuario es profesor, restringe a sus propios grupos."""
    if current_user.is_profesor() and current_user.profesor:
        grupos_qs = grupos_qs.filter_by(profesor_id=current_user.profesor.id)
    return grupos_qs


@honor_bp.route('/')
@login_required
def index():
    """Listado del cuadro de honor con filtros."""
    # Parámetros
    limite = request.args.get('limite', 10, type=int)
    grupo_id = request.args.get('grupo', type=int)
    materia_id = request.args.get('materia', type=int)
    periodo = request.args.get('periodo', '').strip() or None
    anio = request.args.get('anio', type=int)

    # Si es profesor y no pasó grupo, limitar a sus grupos
    grupo_ids_profesor = None
    if current_user.is_profesor() and current_user.profesor:
        grupo_ids_profesor = [g.id for g in current_user.profesor.grupos.all()]
        if grupo_id and grupo_id not in grupo_ids_profesor:
            abort(403)

    # Calcular ranking
    if current_user.is_profesor() and not grupo_id and grupo_ids_profesor:
        # Profesor sin grupo específico: ranking solo sobre sus grupos
        ranking_total = []
        for gid in grupo_ids_profesor:
            sub = CalculoService.top_estudiantes(
                limite=None, grupo_id=gid, periodo=periodo, anio=anio,
            )
            ranking_total.extend(sub)
        # Consolidar por estudiante (si aparece en varios grupos, promediar)
        consolidado = {}
        for r in ranking_total:
            eid = r['estudiante'].id
            if eid not in consolidado:
                consolidado[eid] = {
                    'estudiante': r['estudiante'],
                    'suma': r['promedio'] * r['grupos_evaluados'],
                    'grupos_evaluados': r['grupos_evaluados'],
                    'grupos': list(r['grupos']),
                }
            else:
                consolidado[eid]['suma'] += r['promedio'] * r['grupos_evaluados']
                consolidado[eid]['grupos_evaluados'] += r['grupos_evaluados']
                consolidado[eid]['grupos'].extend(r['grupos'])
        ranking = []
        for c in consolidado.values():
            if c['grupos_evaluados'] > 0:
                ranking.append({
                    'estudiante': c['estudiante'],
                    'promedio': round(c['suma'] / c['grupos_evaluados'], 2),
                    'grupos_evaluados': c['grupos_evaluados'],
                    'grupos': c['grupos'],
                })
        ranking.sort(key=lambda x: x['promedio'], reverse=True)
        ranking = ranking[:limite] if limite else ranking
        # Reasignar posiciones con regla olímpica
        prev_p, prev_pos = None, 0
        for i, item in enumerate(ranking, start=1):
            if prev_p is not None and item['promedio'] == prev_p:
                item['posicion'] = prev_pos
            else:
                item['posicion'] = i
                prev_pos = i
            prev_p = item['promedio']
    else:
        ranking = CalculoService.top_estudiantes(
            limite=limite, grupo_id=grupo_id, materia_id=materia_id,
            periodo=periodo, anio=anio,
        )

    # Datos para los selects de filtro
    grupos_qs = Grupo.query.filter_by(activo=True)
    grupos_qs = _aplicar_filtros_profesor(grupos_qs)
    grupos = grupos_qs.order_by(Grupo.codigo).all()

    materias = Materia.query.filter_by(activa=True).order_by(Materia.nombre).all()

    # Lista distinta de periodos existentes
    periodos = sorted({g.periodo for g in Grupo.query.all() if g.periodo})
    anios = sorted({g.anio for g in Grupo.query.all() if g.anio}, reverse=True)

    return render_template(
        'honor/index.html',
        ranking=ranking,
        grupos=grupos,
        materias=materias,
        periodos=periodos,
        anios=anios,
        limite=limite,
        grupo_id=grupo_id,
        materia_id=materia_id,
        periodo=periodo,
        anio=anio,
    )


@honor_bp.route('/diploma/<int:estudiante_id>')
@login_required
def diploma(estudiante_id):
    """Genera un diploma PDF para un estudiante."""
    grupo_id = request.args.get('grupo', type=int)
    materia_id = request.args.get('materia', type=int)
    periodo = request.args.get('periodo', '').strip() or None
    anio = request.args.get('anio', type=int)

    # Verificar permisos si es profesor
    if current_user.is_profesor() and current_user.profesor:
        if grupo_id:
            grupo = Grupo.query.get_or_404(grupo_id)
            if grupo.profesor_id != current_user.profesor.id:
                abort(403)

    # Recalcular ranking para encontrar la posición del estudiante
    ranking = CalculoService.top_estudiantes(
        limite=None, grupo_id=grupo_id, materia_id=materia_id,
        periodo=periodo, anio=anio,
    )
    item = next((r for r in ranking if r['estudiante'].id == estudiante_id), None)

    if not item:
        # Si el estudiante no está en el ranking (no tiene notas),
        # generar diploma sin posición específica.
        estudiante = Estudiante.query.get_or_404(estudiante_id)
        item = {
            'estudiante': estudiante,
            'posicion': '-',
            'promedio': 0.0,
            'grupos_evaluados': 0,
            'grupos': [],
        }

    pdf_buf = ReporteService.diploma_honor(item, periodo=periodo, anio=anio)
    filename = f"diploma_{item['estudiante'].codigo or item['estudiante'].id}.pdf"

    return send_file(
        pdf_buf, mimetype='application/pdf',
        as_attachment=True, download_name=filename,
    )


@honor_bp.route('/diplomas-lote')
@login_required
def diplomas_lote():
    """
    Genera un PDF único con todos los diplomas del top (un diploma por página).
    """
    limite = request.args.get('limite', 10, type=int)
    grupo_id = request.args.get('grupo', type=int)
    materia_id = request.args.get('materia', type=int)
    periodo = request.args.get('periodo', '').strip() or None
    anio = request.args.get('anio', type=int)

    if current_user.is_profesor() and current_user.profesor:
        if grupo_id:
            grupo = Grupo.query.get_or_404(grupo_id)
            if grupo.profesor_id != current_user.profesor.id:
                abort(403)

    ranking = CalculoService.top_estudiantes(
        limite=limite, grupo_id=grupo_id, materia_id=materia_id,
        periodo=periodo, anio=anio,
    )

    if not ranking:
        abort(404)

    pdf_buf = ReporteService.diplomas_lote(ranking, periodo=periodo, anio=anio)

    filename = f"diplomas_top{len(ranking)}"
    if anio:
        filename += f"_{anio}"
    if periodo:
        filename += f"_{periodo}"
    filename += ".pdf"

    return send_file(
        pdf_buf, mimetype='application/pdf',
        as_attachment=True, download_name=filename,
    )
