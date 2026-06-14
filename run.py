"""
Punto de entrada de la aplicación EduTrack.
Ejecutar con: python run.py
"""
import os
from app import create_app, db
from app.models import (
    Usuario, Profesor, Estudiante, Grupo, Materia,
    Evaluacion, Nota, Asistencia, ProfesorMateria, EstudianteGrupo
)

flask_env = os.getenv('FLASK_ENV')
if not flask_env and os.getenv('DATABASE_URL'):
    flask_env = 'production'
app = create_app(flask_env or 'default')


@app.shell_context_processor
def make_shell_context():
    """Contexto para `flask shell`."""
    return {
        'db': db,
        'Usuario': Usuario,
        'Profesor': Profesor,
        'Estudiante': Estudiante,
        'Grupo': Grupo,
        'Materia': Materia,
        'Evaluacion': Evaluacion,
        'Nota': Nota,
        'Asistencia': Asistencia,
    }



@app.cli.command('run-https')
def run_https():
    """
    Arranca el servidor con HTTPS usando un certificado autofirmado
    (útil para probar la configuración de seguridad localmente).
    Requiere: pip install pyOpenSSL
    """
    try:
        import ssl  # noqa: F401
        # 'adhoc' genera un certificado autofirmado en memoria
        app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
    except (ImportError, Exception) as e:
        print(f'❌ No se pudo iniciar con HTTPS: {e}')
        print('   Instala con: pip install pyOpenSSL')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
