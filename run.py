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

app = create_app(os.getenv('FLASK_ENV') or 'default')


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


@app.cli.command('init-db')
def init_db():
    """Inicializa la base de datos creando todas las tablas."""
    db.create_all()
    print('✓ Base de datos inicializada.')


@app.cli.command('seed-db')
def seed_db():
    """Carga datos de prueba en la base de datos."""
    from app.utils.seed_data import seed_database
    seed_database()
    print('✓ Datos de prueba cargados exitosamente.')


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
    # En producción (Render), el puerto viene en la variable de entorno PORT
    # En desarrollo local, usa 5000
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
