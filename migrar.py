"""Migra de SQLite a PostgreSQL."""
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

PG_URL = os.environ['DATABASE_URL']
SQLITE_URL = 'sqlite:///edutrack.db'

# 1. Crear tablas en PostgreSQL
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('✓ Tablas creadas en PostgreSQL')

# 2. Copiar datos
sq_engine = create_engine(SQLITE_URL)
pg_engine = create_engine(PG_URL)
sq_meta = MetaData(); sq_meta.reflect(bind=sq_engine)
pg_meta = MetaData(); pg_meta.reflect(bind=pg_engine)

ORDEN = [
    'usuarios','profesores','materias','profesor_materia','estudiantes',
    'grupos','estudiante_grupo','evaluaciones','notas','asistencias',
    'intentos_login'
]

SqSession = sessionmaker(bind=sq_engine)
PgSession = sessionmaker(bind=pg_engine)
sq = SqSession(); pg = PgSession()

for tn in ORDEN:
    if tn not in sq_meta.tables:
        continue
    rows = sq.execute(sq_meta.tables[tn].select()).fetchall()
    if not rows:
        continue
    for row in rows:
        try:
            pg.execute(pg_meta.tables[tn].insert().values(**dict(row._mapping)))
        except Exception as e:
            print(f'  ⚠ {tn}: {e}')
    pg.commit()
    print(f'✓ {tn}: {len(rows)} filas')

# 3. Resetear secuencias en PostgreSQL
with pg_engine.connect() as conn:
    for tn in ORDEN:
        if tn not in sq_meta.tables:
            continue
        try:
            conn.execute(
                f"SELECT setval(pg_get_serial_sequence('{tn}','id'),"
                f"(SELECT MAX(id) FROM {tn}))"
            )
        except Exception:
            pass
    conn.commit()

print('\n✅ Migración completada')