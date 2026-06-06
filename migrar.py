"""
Migra datos de SQLite (edutrack.db) a PostgreSQL.

REQUISITOS ANTES DE EJECUTAR:
  1. Tu archivo .env debe tener:
       DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/edutrack
  2. Debes haber instalado: pip install psycopg2-binary
  3. La base de datos 'edutrack' debe existir en PostgreSQL (vacía).
  4. El archivo SQLite 'edutrack.db' debe estar en la carpeta actual o en instance/.

USO:
    python migrar.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

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

# Buscar la BD de SQLite (puede estar en raíz o en instance/)
SQLITE_PATHS = ['edutrack.db', 'instance/edutrack.db']
SQLITE_PATH = None
for p in SQLITE_PATHS:
    if os.path.exists(p):
        SQLITE_PATH = p
        break

if not SQLITE_PATH:
    print('❌ ERROR: No se encontró edutrack.db')
    print('   Asegúrate de tener datos en SQLite primero (ejecuta python setup.py)')
    sys.exit(1)

SQLITE_URL = f'sqlite:///{SQLITE_PATH}'

print(f'📂 SQLite origen: {SQLITE_PATH}')
print(f'🐘 PostgreSQL destino: {PG_URL[:50]}...')
print()

# ============================================================
# 2. Crear tablas en PostgreSQL (usa los modelos de la app)
# ============================================================
print('1️⃣  Creando tablas en PostgreSQL...')

# Forzar que la app use la URL de PostgreSQL al crear tablas
os.environ['DATABASE_URL'] = PG_URL

from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('   ✓ Tablas creadas')

# ============================================================
# 3. Copiar datos tabla por tabla
# ============================================================
print('\n2️⃣  Copiando datos...')

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

sq_engine = create_engine(SQLITE_URL)
pg_engine = create_engine(PG_URL)

sq_meta = MetaData()
sq_meta.reflect(bind=sq_engine)

pg_meta = MetaData()
pg_meta.reflect(bind=pg_engine)

# Orden importante por las foreign keys
ORDEN = [
    'usuarios',
    'profesores',
    'materias',
    'profesor_materia',
    'estudiantes',
    'grupos',
    'estudiante_grupo',
    'evaluaciones',
    'notas',
    'asistencias',
    'intentos_login',
]

SqSession = sessionmaker(bind=sq_engine)
PgSession = sessionmaker(bind=pg_engine)
sq = SqSession()
pg = PgSession()

total_filas = 0
for tn in ORDEN:
    if tn not in sq_meta.tables:
        print(f'   - {tn}: tabla no existe en SQLite, saltando')
        continue
    if tn not in pg_meta.tables:
        print(f'   - {tn}: tabla no existe en PG, saltando')
        continue

    rows = sq.execute(sq_meta.tables[tn].select()).fetchall()
    if not rows:
        print(f'   - {tn}: vacía')
        continue

    errores = 0
    for row in rows:
        try:
            pg.execute(pg_meta.tables[tn].insert().values(**dict(row._mapping)))
        except Exception as e:
            errores += 1
            if errores <= 3:  # solo mostrar primeros 3 errores
                print(f'     ⚠ Error en fila: {str(e)[:80]}')

    pg.commit()
    insertadas = len(rows) - errores
    total_filas += insertadas
    print(f'   ✓ {tn}: {insertadas}/{len(rows)} filas insertadas')

# ============================================================
# 4. Resetear secuencias de PostgreSQL (auto-increment)
# ============================================================
print('\n3️⃣  Reseteando secuencias...')
with pg_engine.connect() as conn:
    for tn in ORDEN:
        if tn not in sq_meta.tables:
            continue
        try:
            from sqlalchemy import text
            conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{tn}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {tn}), 1))"
            ))
        except Exception as e:
            print(f'   - {tn}: sin secuencia ({str(e)[:60]})')
    conn.commit()
print('   ✓ Secuencias actualizadas')

print(f'\n✅ Migración completada — {total_filas} filas transferidas')
print('\nAhora tu app usará PostgreSQL.')
print('Reinicia: python run.py')
