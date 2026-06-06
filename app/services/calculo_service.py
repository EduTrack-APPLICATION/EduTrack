"""
Servicio de cálculos académicos.
Centraliza fórmulas de notas finales, estados académicos y alertas.
"""
from flask import current_app
from sqlalchemy import func
from app import db
from app.models import (
    Nota, Evaluacion, Estudiante, Grupo, Asistencia, EstadoAsistenciaEnum
)


class CalculoService:
    """Servicio para cálculos académicos centralizados."""

    @staticmethod
    def nota_final_estudiante(estudiante_id, grupo_id):
        """
        Calcula nota final ponderada de un estudiante en un grupo.
        Fórmula: Σ (puntaje_obtenido/puntaje_max * 100 * porcentaje_eval/100)
        Retorna un dict con: nota_final, evaluaciones_calificadas, porcentaje_acumulado.
        """
        evaluaciones = Evaluacion.query.filter_by(grupo_id=grupo_id).all()
        if not evaluaciones:
            return {
                'nota_final': 0.0,
                'evaluaciones_total': 0,
                'evaluaciones_calificadas': 0,
                'porcentaje_acumulado': 0.0,
                'porcentaje_pendiente': 100.0,
            }

        nota_final = 0.0
        porcentaje_acumulado = 0.0
        calificadas = 0

        for ev in evaluaciones:
            nota = Nota.query.filter_by(estudiante_id=estudiante_id, evaluacion_id=ev.id).first()
            if nota and ev.puntaje_maximo > 0:
                porcentaje_obtenido = (nota.puntaje / ev.puntaje_maximo) * 100
                aporte = porcentaje_obtenido * (ev.porcentaje / 100)
                nota_final += aporte
                porcentaje_acumulado += ev.porcentaje
                calificadas += 1

        return {
            'nota_final': round(nota_final, 2),
            'evaluaciones_total': len(evaluaciones),
            'evaluaciones_calificadas': calificadas,
            'porcentaje_acumulado': round(porcentaje_acumulado, 2),
            'porcentaje_pendiente': round(100.0 - porcentaje_acumulado, 2),
        }

    @staticmethod
    def estado_academico(nota_final, porcentaje_acumulado=100.0):
        """
        Retorna el estado académico según la nota final.
        - Aprobado: >= NOTA_MINIMA_APROBACION
        - Recuperación: entre NOTA_RECUPERACION y NOTA_MINIMA_APROBACION
        - Reprobado: < NOTA_RECUPERACION
        - En curso: si aún quedan evaluaciones pendientes
        """
        nota_min = current_app.config['NOTA_MINIMA_APROBACION']
        nota_rec = current_app.config['NOTA_RECUPERACION']

        if porcentaje_acumulado < 100:
            if nota_final >= nota_min:
                return ('en_curso_aprobando', 'En curso (aprobando)', 'info')
            elif nota_final >= nota_rec:
                return ('en_curso_riesgo', 'En curso (en riesgo)', 'warning')
            else:
                return ('en_curso_critico', 'En curso (crítico)', 'danger')

        if nota_final >= nota_min:
            return ('aprobado', 'Aprobado', 'success')
        elif nota_final >= nota_rec:
            return ('recuperacion', 'Recuperación', 'warning')
        else:
            return ('reprobado', 'Reprobado', 'danger')

    @staticmethod
    def porcentaje_asistencia(estudiante_id, grupo_id):
        """Retorna el % de asistencia de un estudiante en un grupo."""
        total = Asistencia.query.filter_by(
            estudiante_id=estudiante_id, grupo_id=grupo_id
        ).count()
        if total == 0:
            return None
        presentes = Asistencia.query.filter(
            Asistencia.estudiante_id == estudiante_id,
            Asistencia.grupo_id == grupo_id,
            Asistencia.estado.in_([
                EstadoAsistenciaEnum.PRESENTE.value,
                EstadoAsistenciaEnum.JUSTIFICADO.value,
                EstadoAsistenciaEnum.TARDIA.value
            ])
        ).count()
        return round((presentes / total) * 100, 2)

    @staticmethod
    def estudiantes_en_riesgo(profesor_id=None):
        """
        Retorna lista de estudiantes en riesgo académico
        (nota_final < NOTA_MINIMA_APROBACION en al menos un grupo).
        """
        nota_min = current_app.config['NOTA_MINIMA_APROBACION']
        en_riesgo = []

        query = Grupo.query.filter_by(activo=True)
        if profesor_id:
            query = query.filter_by(profesor_id=profesor_id)
        grupos = query.all()

        for grupo in grupos:
            for est in grupo.estudiantes:
                calc = CalculoService.nota_final_estudiante(est.id, grupo.id)
                if calc['evaluaciones_calificadas'] > 0 and calc['nota_final'] < nota_min:
                    en_riesgo.append({
                        'estudiante': est,
                        'grupo': grupo,
                        'nota_final': calc['nota_final'],
                        'porcentaje_acumulado': calc['porcentaje_acumulado'],
                    })
        return en_riesgo

    @staticmethod
    def promedio_general(profesor_id=None):
        """Promedio general de todas las notas (ponderado por evaluación)."""
        query = db.session.query(
            func.avg(Nota.puntaje * 100.0 / Evaluacion.puntaje_maximo)
        ).select_from(Nota).join(Evaluacion, Nota.evaluacion_id == Evaluacion.id)
        if profesor_id:
            query = query.filter(Evaluacion.profesor_id == profesor_id)
        resultado = query.scalar()
        return round(resultado, 2) if resultado else 0.0

    @staticmethod
    def alertas_estudiante(estudiante_id):
        """Genera lista de alertas para un estudiante."""
        alertas = []
        nota_min = current_app.config['NOTA_MINIMA_APROBACION']
        asist_min = current_app.config['ASISTENCIA_MINIMA']

        estudiante = Estudiante.query.get(estudiante_id)
        if not estudiante:
            return alertas

        for grupo in estudiante.grupos:
            calc = CalculoService.nota_final_estudiante(estudiante_id, grupo.id)
            if calc['evaluaciones_calificadas'] > 0 and calc['nota_final'] < nota_min:
                alertas.append({
                    'tipo': 'rendimiento',
                    'nivel': 'danger',
                    'mensaje': f'Bajo rendimiento en {grupo.materia.nombre} ({calc["nota_final"]:.1f})',
                    'grupo_id': grupo.id,
                })

            asist = CalculoService.porcentaje_asistencia(estudiante_id, grupo.id)
            if asist is not None and asist < asist_min:
                alertas.append({
                    'tipo': 'asistencia',
                    'nivel': 'warning',
                    'mensaje': f'Asistencia baja en {grupo.materia.nombre} ({asist:.1f}%)',
                    'grupo_id': grupo.id,
                })

        return alertas

    @staticmethod
    def top_estudiantes(limite=10, grupo_id=None, materia_id=None,
                        periodo=None, anio=None, solo_con_notas=True):
        """
        Retorna el ranking de estudiantes ordenado por promedio general descendente.

        Parámetros:
            limite (int): número máximo de estudiantes a retornar (None = todos).
            grupo_id (int): filtrar por un grupo específico.
            materia_id (int): filtrar por una materia (todos sus grupos).
            periodo (str): filtrar por periodo académico (ej: '2026-I').
            anio (int): filtrar por año.
            solo_con_notas (bool): excluir estudiantes sin notas registradas.

        Retorna lista de dicts:
            { 'posicion': int, 'estudiante': Estudiante, 'promedio': float,
              'grupos_evaluados': int, 'grupos': [(Grupo, nota_final)] }
        """
        grupos_qs = Grupo.query.filter_by(activo=True)
        if grupo_id:
            grupos_qs = grupos_qs.filter(Grupo.id == grupo_id)
        if materia_id:
            grupos_qs = grupos_qs.filter(Grupo.materia_id == materia_id)
        if periodo:
            grupos_qs = grupos_qs.filter(Grupo.periodo == periodo)
        if anio:
            grupos_qs = grupos_qs.filter(Grupo.anio == anio)
        grupos = grupos_qs.all()

        if not grupos:
            return []

        estudiante_data = {}

        for grupo in grupos:
            for est in grupo.estudiantes:
                calc = CalculoService.nota_final_estudiante(est.id, grupo.id)

                if solo_con_notas and calc['evaluaciones_calificadas'] == 0:
                    continue

                if est.id not in estudiante_data:
                    estudiante_data[est.id] = {
                        'estudiante': est,
                        'suma_notas': 0.0,
                        'grupos_evaluados': 0,
                        'grupos': [],
                    }

                data = estudiante_data[est.id]
                data['suma_notas'] += calc['nota_final']
                data['grupos_evaluados'] += 1
                data['grupos'].append((grupo, calc['nota_final']))

        ranking = []
        for data in estudiante_data.values():
            if data['grupos_evaluados'] == 0:
                continue
            promedio = data['suma_notas'] / data['grupos_evaluados']
            ranking.append({
                'estudiante': data['estudiante'],
                'promedio': round(promedio, 2),
                'grupos_evaluados': data['grupos_evaluados'],
                'grupos': data['grupos'],
            })

        ranking.sort(key=lambda x: x['promedio'], reverse=True)

        if limite:
            ranking = ranking[:limite]

        # Asignar posición con manejo de empates (regla olímpica)
        prev_promedio = None
        prev_posicion = 0
        for i, item in enumerate(ranking, start=1):
            if prev_promedio is not None and item['promedio'] == prev_promedio:
                item['posicion'] = prev_posicion
            else:
                item['posicion'] = i
                prev_posicion = i
            prev_promedio = item['promedio']

        return ranking
