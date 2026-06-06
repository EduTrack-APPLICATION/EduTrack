"""
Validador de contraseñas con análisis de fuerza.
"""
import re


# Contraseñas extremadamente comunes que NUNCA se deben permitir
PASSWORDS_PROHIBIDAS = {
    '12345678', '123456789', '1234567890', 'password', 'password1', 'password123',
    'qwerty123', 'qwertyuiop', 'admin', 'admin123', 'administrator',
    'profesor', 'profesor123', 'estudiante', 'estudiante123',
    'letmein', 'welcome', 'welcome123', 'monkey', 'dragon', 'master',
    '11111111', '00000000', 'abc12345', 'iloveyou',
    'edutrack', 'edutrack123', 'colegio', 'escuela', 'colegio123',
}


def validar_password(password, nombre_usuario=None, email=None):
    """
    Valida una contraseña.
    Retorna (es_valida: bool, errores: list[str]).
    """
    errores = []

    if not password:
        return False, ['La contraseña es obligatoria.']

    if len(password) < 8:
        errores.append('Debe tener al menos 8 caracteres.')

    if not re.search(r'[A-Z]', password):
        errores.append('Debe incluir al menos una letra mayúscula.')

    if not re.search(r'[a-z]', password):
        errores.append('Debe incluir al menos una letra minúscula.')

    if not re.search(r'\d', password):
        errores.append('Debe incluir al menos un número.')

    if password.lower() in PASSWORDS_PROHIBIDAS:
        errores.append('Esta contraseña es muy común. Elige una más segura.')

    # No debe contener el username o email
    if nombre_usuario and len(nombre_usuario) >= 4 and \
       nombre_usuario.lower() in password.lower():
        errores.append('La contraseña no debe contener tu nombre de usuario.')

    if email:
        local_email = email.split('@')[0].lower()
        if len(local_email) >= 4 and local_email in password.lower():
            errores.append('La contraseña no debe contener tu email.')

    return len(errores) == 0, errores


def calcular_fuerza(password):
    """
    Calcula la fuerza de una contraseña.
    Retorna: { 'score': 0-4, 'label': str, 'color': str }
      - 0: vacía
      - 1: muy débil (rojo)
      - 2: débil (naranja)
      - 3: aceptable (amarillo)
      - 4: fuerte (verde)
    """
    if not password:
        return {'score': 0, 'label': 'Vacía', 'color': 'muted'}

    score = 0
    if len(password) >= 8:  score += 1
    if len(password) >= 12: score += 1
    if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password): score += 1
    if re.search(r'\d', password): score += 1
    if re.search(r'[^A-Za-z0-9]', password): score += 1

    # Penalización por contraseñas comunes
    if password.lower() in PASSWORDS_PROHIBIDAS:
        score = 1

    score = min(score, 4)

    etiquetas = {
        1: ('Muy débil',  'danger'),
        2: ('Débil',      'warning'),
        3: ('Aceptable',  'info'),
        4: ('Fuerte',     'success'),
    }
    label, color = etiquetas.get(score, ('Muy débil', 'danger'))
    return {'score': score, 'label': label, 'color': color}
