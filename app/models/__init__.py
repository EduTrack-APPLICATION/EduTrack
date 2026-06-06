"""
Modelos de datos de EduTrack.
"""
from app.models.usuario import Usuario, RolEnum
from app.models.profesor import Profesor, ProfesorMateria
from app.models.estudiante import Estudiante, EstadoEstudianteEnum
from app.models.grupo import Grupo, EstudianteGrupo
from app.models.materia import Materia
from app.models.evaluacion import Evaluacion, TipoEvaluacionEnum
from app.models.nota import Nota
from app.models.asistencia import Asistencia, EstadoAsistenciaEnum
from app.models.intento_login import IntentoLogin
from app.models.configuracion import Configuracion

__all__ = [
    'Usuario', 'RolEnum',
    'Profesor', 'ProfesorMateria',
    'Estudiante', 'EstadoEstudianteEnum',
    'Grupo', 'EstudianteGrupo',
    'Materia',
    'Evaluacion', 'TipoEvaluacionEnum',
    'Nota',
    'Asistencia', 'EstadoAsistenciaEnum',
    'IntentoLogin',
    'Configuracion',
]
