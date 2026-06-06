"""
Setup automático para EduTrack.

Uso (la primera vez, después de descomprimir el ZIP):
    python setup.py

Esto hace:
  1. Crea el archivo .env si no existe.
  2. Verifica que las dependencias estén instaladas.
  3. Crea las tablas de la base de datos SQLite.
  4. Carga datos de prueba.

Tras correrlo, simplemente ejecuta:
    python run.py
"""
import os
import sys
import secrets


def banner(texto):
    print()
    print('=' * 60)
    print(' ' + texto)
    print('=' * 60)


def paso(numero, texto):
    print(f'\n[{numero}] {texto}')


def ok(mensaje):
    print(f'    ✓ {mensaje}')


def aviso(mensaje):
    print(f'    ⚠ {mensaje}')


def error(mensaje):
    print(f'    ✗ {mensaje}')


def main():
    banner('Setup automático de EduTrack')

    # =========================================================
    # PASO 1: Verificar versión de Python
    # =========================================================
    paso(1, 'Verificando Python...')
    py_version = sys.version_info
    if py_version < (3, 9):
        error(f'Python 3.9 o superior requerido. Tienes {py_version.major}.{py_version.minor}')
        sys.exit(1)
    ok(f'Python {py_version.major}.{py_version.minor}.{py_version.micro}')

    # =========================================================
    # PASO 2: Crear archivo .env si no existe
    # =========================================================
    paso(2, 'Configurando archivo .env...')
    env_path = '.env'
    if os.path.exists(env_path):
        ok('.env ya existe (no se sobrescribe)')
    else:
        secret = secrets.token_hex(32)
        contenido = f"""FLASK_APP=run.py
FLASK_ENV=development
FLASK_CONFIG=development
SECRET_KEY={secret}
DATABASE_URL=sqlite:///edutrack.db
"""
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        ok('.env creado con SECRET_KEY aleatoria')

    # =========================================================
    # PASO 3: Verificar dependencias clave
    # =========================================================
    paso(3, 'Verificando dependencias...')
    deps_faltantes = []
    for mod in ('flask', 'flask_sqlalchemy', 'flask_login', 'flask_bcrypt',
                'flask_wtf', 'flask_migrate', 'reportlab', 'openpyxl',
                'dotenv', 'email_validator', 'pyotp', 'qrcode', 'flask_mail'):
        try:
            __import__(mod)
        except ImportError:
            deps_faltantes.append(mod)

    if deps_faltantes:
        error(f'Faltan dependencias: {", ".join(deps_faltantes)}')
        print('\n    Ejecuta primero:')
        print('        pip install -r requirements.txt\n')
        sys.exit(1)
    ok('Todas las dependencias están instaladas')

    # =========================================================
    # PASO 4: Cargar la app y crear tablas
    # =========================================================
    paso(4, 'Creando base de datos SQLite...')

    # Forzar carga del .env recién creado
    from dotenv import load_dotenv
    load_dotenv(override=True)

    try:
        from app import create_app, db
        app = create_app('development')
        with app.app_context():
            db.create_all()
        ok(f'Base de datos creada: {app.config["SQLALCHEMY_DATABASE_URI"]}')
    except Exception as e:
        error(f'No se pudo crear la BD: {e}')
        sys.exit(1)

    # =========================================================
    # PASO 5: Cargar datos de prueba
    # =========================================================
    paso(5, 'Cargando datos de prueba...')
    try:
        from app.models import Usuario
        with app.app_context():
            if Usuario.query.count() > 0:
                aviso('La BD ya tiene datos — saltando carga inicial')
            else:
                from app.utils.seed_data import seed_database
                seed_database()
                ok('Datos de prueba cargados')
    except Exception as e:
        error(f'No se pudieron cargar los datos: {e}')
        sys.exit(1)

    # =========================================================
    # ¡Listo!
    # =========================================================
    banner('¡EduTrack está listo!')
    print("""
    Ahora arranca el servidor con:

        python run.py

    Luego abre tu navegador en:

        http://127.0.0.1:5000

    Inicia sesión con:

        Admin:    usuario = admin       contraseña = admin123
        Profesor: usuario = mrodriguez  contraseña = profesor123
""")


if __name__ == '__main__':
    main()
