"""
Setup de producción: crea las tablas en la BD configurada (SQLite o PostgreSQL)
y genera los usuarios iniciales SIN cargar datos de prueba.

Uso:
    python setup_produccion.py                  # interactivo: pide credenciales
    python setup_produccion.py --auto           # automático: genera contraseñas aleatorias
    python setup_produccion.py --auto --force   # incluso si ya existen admins

Crea:
    - 1 admin       (rol ADMIN)
    - 2 super_admin (rol SUPER_ADMIN — acceso al panel del developer)
"""
import os
import sys
import secrets
import string
from getpass import getpass

# CARGAR .env ANTES de importar la app — necesario para que DATABASE_URL llegue
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app, db
from app.models import Usuario, RolEnum


# ============================================================
# Helpers
# ============================================================

def _generar_password(longitud=14):
    """Contraseña segura: letras+números, sin chars confusos (0, O, 1, l, I)."""
    chars = ''.join(c for c in (string.ascii_letters + string.digits)
                     if c not in '0O1lI')
    # Asegurar al menos: 1 mayús, 1 minús, 1 dígito
    while True:
        pw = ''.join(secrets.choice(chars) for _ in range(longitud))
        if (any(c.islower() for c in pw) and
            any(c.isupper() for c in pw) and
            any(c.isdigit() for c in pw)):
            return pw


def _imprimir_separador(titulo=''):
    if titulo:
        print(f'\n{"═" * 60}')
        print(f' {titulo}')
        print(f'{"═" * 60}\n')
    else:
        print('─' * 60)


def _crear_usuario(username, email, nombre, rol, password, forzar_cambio=True):
    """Crea un usuario y lo guarda. Retorna el usuario o None si ya existe."""
    if Usuario.query.filter_by(username=username).first():
        print(f'  ⚠ El usuario "{username}" ya existe — se omite.')
        return None
    if Usuario.query.filter_by(email=email).first():
        print(f'  ⚠ El email "{email}" ya está en uso — se omite.')
        return None

    u = Usuario(
        username=username,
        email=email,
        nombre_completo=nombre,
        rol=rol,
        forzar_cambio_password=forzar_cambio,
        activo=True,
    )
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u


def _pedir(prompt, default=None, requerido=True):
    """Lee entrada del usuario, con default y validación."""
    while True:
        sufijo = f' [{default}]' if default else ''
        valor = input(f'{prompt}{sufijo}: ').strip()
        if not valor and default:
            return default
        if not valor and requerido:
            print('   ❌ Este campo es obligatorio.')
            continue
        return valor


def _pedir_password(label='Contraseña'):
    """Lee contraseña con confirmación."""
    while True:
        p1 = getpass(f'{label} (mín. 8 caracteres): ')
        if len(p1) < 8:
            print('   ❌ Mínimo 8 caracteres.')
            continue
        p2 = getpass(f'Confirma {label.lower()}: ')
        if p1 != p2:
            print('   ❌ No coinciden, intenta de nuevo.')
            continue
        return p1


# ============================================================
# Modos de creación
# ============================================================

def crear_interactivo():
    """Pide credenciales una por una."""
    usuarios = []

    _imprimir_separador('Configuración de usuarios iniciales')
    print('Vas a crear 1 administrador y 2 super-administradores.')
    print('Las contraseñas no se muestran al escribir.\n')

    # ADMIN
    print('━━━ Administrador (1 de 3) ━━━')
    username = _pedir('Usuario', 'admin')
    email    = _pedir('Email', 'admin@tucolegio.com')
    nombre   = _pedir('Nombre completo', 'Administrador General')
    pw       = _pedir_password()
    usuarios.append({
        'username': username, 'email': email, 'nombre': nombre,
        'rol': RolEnum.ADMIN.value, 'password': pw,
    })

    # SUPER_ADMIN 1
    print('\n━━━ Super-administrador 1 (2 de 3) ━━━')
    username = _pedir('Usuario', 'developer')
    email    = _pedir('Email', 'dev@tucolegio.com')
    nombre   = _pedir('Nombre completo', 'Developer')
    pw       = _pedir_password()
    usuarios.append({
        'username': username, 'email': email, 'nombre': nombre,
        'rol': RolEnum.SUPER_ADMIN.value, 'password': pw,
    })

    # SUPER_ADMIN 2
    print('\n━━━ Super-administrador 2 (3 de 3) ━━━')
    username = _pedir('Usuario', 'developer2')
    email    = _pedir('Email', 'dev2@tucolegio.com')
    nombre   = _pedir('Nombre completo', 'Developer Backup')
    pw       = _pedir_password()
    usuarios.append({
        'username': username, 'email': email, 'nombre': nombre,
        'rol': RolEnum.SUPER_ADMIN.value, 'password': pw,
    })

    return usuarios


def crear_automatico():
    """Genera credenciales aleatorias."""
    return [
        {
            'username': 'admin',
            'email': 'admin@edutrack.local',
            'nombre': 'Administrador General',
            'rol': RolEnum.ADMIN.value,
            'password': _generar_password(),
        },
        {
            'username': 'developer',
            'email': 'developer@edutrack.local',
            'nombre': 'Developer Principal',
            'rol': RolEnum.SUPER_ADMIN.value,
            'password': _generar_password(),
        },
        {
            'username': 'developer2',
            'email': 'developer2@edutrack.local',
            'nombre': 'Developer Backup',
            'rol': RolEnum.SUPER_ADMIN.value,
            'password': _generar_password(),
        },
    ]


# ============================================================
# Main
# ============================================================

def main():
    args = sys.argv[1:]
    modo_auto = '--auto' in args
    force = '--force' in args

    print('\n' + '═' * 60)
    print(' EduTrack — Setup de producción')
    print('═' * 60)

    # 1. Verificar entorno
    print('\n[1] Verificando configuración...')

    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Ocultar contraseña en la URL para mostrarla
        safe = db_url
        if '@' in safe and '://' in safe:
            prefix, rest = safe.split('://', 1)
            if ':' in rest.split('@')[0]:
                user, host = rest.split('@', 1)
                user_name = user.split(':')[0]
                safe = f'{prefix}://{user_name}:***@{host}'
        print(f'    ✓ DATABASE_URL detectada: {safe}')
        if 'postgres' in db_url:
            print(f'    → Usando PostgreSQL')
        else:
            print(f'    → Usando: {db_url[:30]}...')
    else:
        print('    ⚠ DATABASE_URL no configurada → se usará SQLite (edutrack.db)')

    # 2. Crear app y tablas
    print('\n[2] Inicializando base de datos...')
    app = create_app('development')
    with app.app_context():
        try:
            db.create_all()
            print('    ✓ Tablas creadas/verificadas.')
        except Exception as e:
            print(f'    ❌ Error creando tablas: {e}')
            print('\n    Si usas PostgreSQL, verifica que:')
            print('    - El servicio esté corriendo')
            print('    - El usuario tenga permisos: GRANT ALL ON SCHEMA public TO tu_usuario;')
            print('    - La base de datos exista')
            sys.exit(1)

        # 3. Verificar si ya hay admins
        existing = Usuario.query.filter(
            Usuario.rol.in_([RolEnum.ADMIN.value, RolEnum.SUPER_ADMIN.value])
        ).count()

        if existing > 0 and not force:
            print(f'\n[3] Ya existen {existing} administrador(es) en la BD.')
            print('    Para crear más de todos modos, usa: --force')
            print('    Para resetear todo: borra la BD primero.')
            r = input('\n    ¿Continuar y crear los usuarios igualmente? (s/N): ')
            if r.lower() != 's':
                print('\n  Cancelado.')
                return

        # 4. Obtener datos
        print('\n[3] Generando usuarios...')
        if modo_auto:
            print('    Modo automático: contraseñas aleatorias seguras')
            usuarios = crear_automatico()
        else:
            usuarios = crear_interactivo()

        # 5. Crear
        print('\n[4] Insertando en la BD...\n')
        creados = []
        for data in usuarios:
            u = _crear_usuario(
                username=data['username'],
                email=data['email'],
                nombre=data['nombre'],
                rol=data['rol'],
                password=data['password'],
                forzar_cambio=True,
            )
            if u:
                creados.append((u, data['password']))
                rol_label = '👤 ADMIN' if u.rol == RolEnum.ADMIN.value else '⚡ SUPER ADMIN'
                print(f'  ✓ {rol_label}  {u.username}  ({u.nombre_completo})')

        # 6. Mostrar resumen con credenciales (solo modo auto, o si no se quieren ocultar)
        if modo_auto and creados:
            _imprimir_separador('🔐 CREDENCIALES GENERADAS — GUARDA ESTOS DATOS YA')
            print('Estas contraseñas NO se volverán a mostrar.\n')
            for u, pw in creados:
                rol = 'ADMIN' if u.rol == RolEnum.ADMIN.value else 'SUPER_ADMIN'
                print(f'  ┌─ {rol}')
                print(f'  │  Usuario:     {u.username}')
                print(f'  │  Email:       {u.email}')
                print(f'  │  Contraseña:  {pw}')
                print(f'  └─')
                print()
            print('⚠ El primer login obligará a cambiar la contraseña por seguridad.')

        # 7. Final
        _imprimir_separador('✅ Setup completado')
        print(f'  {len(creados)} usuario(s) creado(s)')
        print(f'  Base de datos: lista (sin datos de prueba)')
        print()
        print('  Arranca el servidor con:')
        print('      python run.py')
        print()
        print('  Luego abre tu navegador en:')
        print('      http://127.0.0.1:5000')
        print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n  Cancelado por el usuario.')
        sys.exit(0)
