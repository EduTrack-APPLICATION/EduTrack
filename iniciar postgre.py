"""
Crea tablas y datos de prueba directamente en PostgreSQL.

REQUISITOS ANTES DE EJECUTAR:
  1. Tu archivo .env debe tener:
       DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/edutrack
  2. Debes haber instalado: pip install psycopg2-binary
  3. La base de datos 'edutrack' debe existir en PostgreSQL (vacía).

USO:
    python iniciar postgre.py
"""
import os
import sys
from dotenv import load_dotenv

# Cargar .env desde la carpeta padre
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ============================================================
# 1. Validar configuración
# ============================================================
PG_URL = os.environ.get('DATABASE_URL')

if not PG_URL:
    print('❌ ERROR: No se encontró DATABASE_URL en tu archivo .env')
    print('   Edita el archivo .env y agrega esta línea:')
    print('   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/edutrack')
    sys.exit(1)

if 'postgres' not in PG_URL:
    print(f'❌ ERROR: DATABASE_URL no parece de PostgreSQL: {PG_URL}')
    sys.exit(1)

# Arreglar postgres:// → postgresql:// si viene de Heroku/Render
if PG_URL.startswith('postgres://'):
    PG_URL = PG_URL.replace('postgres://', 'postgresql://', 1)

print(f'🐘 PostgreSQL destino: {PG_URL[:50]}...')
print()

# ============================================================
# 2. Crear tablas en PostgreSQL (usa los modelos de la app)
# ============================================================
print('1️⃣  Creando tablas en PostgreSQL...')

# Forzar que la app use la URL de PostgreSQL
os.environ['DATABASE_URL'] = PG_URL

from app import create_app, db
app = create_app('development')

with app.app_context():
    # Crear todas las tablas
    db.create_all()
    print('   ✓ Tablas creadas')
    
    # ============================================================
    # 3. Cargar datos de prueba
    # ============================================================
    print('\n2️⃣  Cargando datos de prueba...')
    
    from app.utils.seed_data import seed_database
    seed_database()
    
    print('   ✓ Datos cargados')

print('\n✅ Setup completado — PostgreSQL listo con datos de prueba')
print('\nAhora tu app usará PostgreSQL.')
print('Reinicia: python run.py')
