"""
Helpers para gestionar cuentas del portal del estudiante.
Función compartida entre el endpoint de creación, el script CLI y el botón manual.
"""
import secrets
import string

from app import db
from app.models import Usuario, Estudiante, RolEnum


def _generar_password(longitud=10):
    """Genera contraseña fácil de leer (sin chars confusos: 0, O, 1, l, I)."""
    chars = ''.join(c for c in (string.ascii_letters + string.digits)
                     if c not in '0O1lI')
    return ''.join(secrets.choice(chars) for _ in range(longitud))


def _unique_email(base_email, codigo):
    """Retorna un email único: usa el del estudiante si está libre, si no, uno fallback."""
    if base_email and not Usuario.query.filter_by(email=base_email).first():
        return base_email
    candidato = f'{codigo.lower()}@estudiante.local'
    if not Usuario.query.filter_by(email=candidato).first():
        return candidato
    # Último recurso: sufijo aleatorio
    return f'{codigo.lower()}-{secrets.token_hex(3)}@estudiante.local'


def generar_cuenta_estudiante(estudiante, reset=False, commit=True):
    """
    Crea (o resetea) la cuenta del portal para un estudiante.

    Retorna:
        dict con {usuario, password, creada (True si nueva), reset (True si reset)}
        o None si el estudiante ya tenía cuenta y reset=False.
    """
    existente = Usuario.query.filter_by(estudiante_id=estudiante.id).first()

    if existente and not reset:
        return None  # Ya tiene cuenta, no se sobrescribe sin permiso

    password = _generar_password()

    if existente:
        existente.set_password(password)
        existente.forzar_cambio_password = True
        existente.intentos_fallidos = 0
        existente.bloqueado_hasta = None
        existente.activo = True
        if commit:
            db.session.commit()
        return {
            'usuario': existente,
            'username': existente.username,
            'password': password,
            'creada': False,
            'reset': True,
        }

    # Crear cuenta nueva — username = cédula (consistente con profesores)
    # Si no hay cédula o ya existe, usar el código como fallback
    username = (estudiante.cedula or '').strip() or estudiante.codigo
    if Usuario.query.filter_by(username=username).first():
        # Si hay conflicto, intentar con el código
        if username != estudiante.codigo and \
           not Usuario.query.filter_by(username=estudiante.codigo).first():
            username = estudiante.codigo
        else:
            # Último recurso: agregar sufijo aleatorio
            username = f'{username}-{secrets.token_hex(2)}'

    email = _unique_email(estudiante.email, estudiante.codigo)

    u = Usuario(
        username=username,
        email=email,
        nombre_completo=estudiante.nombre_completo,
        rol=RolEnum.ESTUDIANTE.value,
        estudiante_id=estudiante.id,
        forzar_cambio_password=True,
        activo=True,
    )
    u.set_password(password)
    db.session.add(u)
    if commit:
        db.session.commit()

    return {
        'usuario': u,
        'username': username,
        'password': password,
        'creada': True,
        'reset': False,
    }


def tiene_cuenta_portal(estudiante):
    """Retorna True si el estudiante ya tiene cuenta del portal."""
    return Usuario.query.filter_by(estudiante_id=estudiante.id).first() is not None
