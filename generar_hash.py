"""Genera hashes bcrypt para usuarios."""
from flask_bcrypt import Bcrypt
from app import create_app
from datetime import datetime

app = create_app('production')
bcrypt = Bcrypt(app)

# Genera los hashes para las contraseñas
usuarios = [
    {'username': 'danier', 'password': 'Danier2026', 'nombre_completo': 'Danier Admin', 'email': 'danier@edutrack.local'},
    {'username': 'andrick', 'password': 'Andrick2026', 'nombre_completo': 'Andrick Admin', 'email': 'andrick@edutrack.local'},
]

print("Copiar y ejecutar en PostgreSQL (Neon SQL Editor):\n")
print("=" * 80)

for user in usuarios:
    password_hash = bcrypt.generate_password_hash(user['password']).decode('utf-8')
    now = datetime.utcnow().isoformat()
    
    sql = f"""INSERT INTO usuarios (username, email, password_hash, nombre_completo, rol, activo, forzar_cambio_password, totp_habilitado, intentos_fallidos, fecha_creacion, fecha_actualizacion)
VALUES ('{user['username']}', '{user['email']}', '{password_hash}', '{user['nombre_completo']}', 'super_admin', true, true, false, 0, NOW(), NOW());"""
    
    print(sql)
    print()

print("=" * 80)
print("\n✅ Copia los comandos INSERT arriba y ejecútalos en Neon SQL Editor")
print("   https://console.neon.tech → SQL Editor")
