# Migración a PostgreSQL — Guía paso a paso

EduTrack viene con SQLite por defecto (cero configuración). Si quieres usar PostgreSQL, tienes tres opciones.

---

## Opción A — PostgreSQL en la nube (Neon) — recomendado

**Ventajas:** Sin instalación local, 0.5 GB gratis, backups automáticos, conexión desde cualquier máquina.

### Pasos

1. **Crea cuenta en Neon**
   - Ve a https://neon.tech
   - Sign up con GitHub o Google

2. **Crea un proyecto**
   - Click en "Create a project"
   - Nombre: `edutrack`
   - Region: la más cercana (US East para Costa Rica)

3. **Copia el connection string**
   - En el dashboard verás algo como:
     ```
     postgresql://user:pass@ep-xxxxx.us-east-2.aws.neon.tech/edutrack?sslmode=require
     ```

4. **Edita tu `.env`** (crea uno si no existe, copiando `.env.example`):
   ```env
   DATABASE_URL=postgresql://user:pass@ep-xxxxx.us-east-2.aws.neon.tech/edutrack?sslmode=require
   ```

5. **Instala `psycopg2-binary`**:
   ```powershell
   .venv\Scripts\Activate
   pip install psycopg2-binary
   ```

6. **Crea las tablas y carga datos demo**:
   ```powershell
   python setup.py
   ```

7. **Arranca**:
   ```powershell
   python run.py
   ```

Listo.

---

## Opción B — PostgreSQL local (Windows)

**Ventajas:** Sin internet, control total. **Desventaja:** Tienes que instalarlo.

### Pasos

1. **Descarga el instalador**
   - https://www.postgresql.org/download/windows/
   - Versión 16 o más reciente

2. **Durante la instalación**
   - Acepta valores por defecto (puerto **5432**)
   - **Anota la contraseña del usuario `postgres`** que pongas
   - Asegúrate de instalar **pgAdmin** (incluido)

3. **Crea la base de datos** desde PowerShell:
   ```powershell
   # Buscar psql en el menú inicio, o usar:
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
   ```

   Dentro de `psql`:
   ```sql
   CREATE DATABASE edutrack;
   CREATE USER edutrack_user WITH PASSWORD 'tu_password_aqui';
   GRANT ALL PRIVILEGES ON DATABASE edutrack TO edutrack_user;
   \c edutrack
   GRANT ALL ON SCHEMA public TO edutrack_user;
   \q
   ```

4. **Edita tu `.env`**:
   ```env
   DATABASE_URL=postgresql://edutrack_user:tu_password_aqui@localhost:5432/edutrack
   ```

5. **Instala el driver Python**:
   ```powershell
   pip install psycopg2-binary
   ```

6. **Crea tablas + datos demo**:
   ```powershell
   python setup.py
   ```

---

## Opción C — Migrar datos existentes de SQLite a PostgreSQL

Si ya tienes datos en `edutrack.db` (SQLite) que quieres preservar al migrar:

1. Sigue Opción A o B **hasta el paso de instalar `psycopg2-binary`** (NO ejecutes `setup.py` todavía).

2. Crea el script `migrar.py` en la raíz del proyecto:

   ```python
   """Migra de SQLite a PostgreSQL."""
   import os
   from sqlalchemy import create_engine, MetaData
   from sqlalchemy.orm import sessionmaker
   from dotenv import load_dotenv
   load_dotenv()

   PG_URL = os.environ['DATABASE_URL']
   SQLITE_URL = 'sqlite:///edutrack.db'

   # 1. Crear tablas en PG
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

   ORDEN = ['usuarios','profesores','materias','profesor_materia','estudiantes',
            'grupos','estudiante_grupo','evaluaciones','notas','asistencias',
            'intentos_login']

   SqSession = sessionmaker(bind=sq_engine)
   PgSession = sessionmaker(bind=pg_engine)
   sq = SqSession(); pg = PgSession()

   for tn in ORDEN:
       if tn not in sq_meta.tables: continue
       rows = sq.execute(sq_meta.tables[tn].select()).fetchall()
       if not rows: continue
       for row in rows:
           try:
               pg.execute(pg_meta.tables[tn].insert().values(**dict(row._mapping)))
           except Exception as e:
               print(f'  ⚠ {tn}: {e}')
       pg.commit()
       print(f'✓ {tn}: {len(rows)} filas')

   # 3. Resetear secuencias
   with pg_engine.connect() as conn:
       for tn in ORDEN:
           if tn not in sq_meta.tables: continue
           try:
               conn.execute(
                   f"SELECT setval(pg_get_serial_sequence('{tn}','id'),"
                   f"(SELECT MAX(id) FROM {tn}))"
               )
           except Exception: pass
       conn.commit()
   print('\n✅ Migración completada')
   ```

3. Ejecuta:
   ```powershell
   python migrar.py
   ```

---

## Verificar que funciona

Arranca el servidor:

```powershell
python run.py
```

Si todo está bien, verás algo como:
```
 * Running on http://127.0.0.1:5000
```

Entra con `admin` / `admin123`. La app debería funcionar idéntica, pero ahora con PostgreSQL.

---

## Volver a SQLite

Si quieres volver, simplemente **comenta** la línea `DATABASE_URL=...` en tu `.env`:

```env
# DATABASE_URL=postgresql://...
```

Al reiniciar, EduTrack vuelve a usar `edutrack.db` automáticamente.

---

## Solución a problemas comunes

**`could not connect to server`**
→ PostgreSQL no está corriendo. En Windows: abre **Servicios** (`services.msc`), busca `postgresql-x64-XX`, click derecho → Iniciar.

**`password authentication failed for user "postgres"`**
→ La contraseña en `DATABASE_URL` no coincide. Usa la que pusiste durante la instalación.

**`could not translate host name`**
→ Hay un error de tipeo en `DATABASE_URL`. Verifica que no haya espacios al inicio.

**`No module named 'psycopg2'`**
→ Falta instalar el driver: `pip install psycopg2-binary`

**`relation "usuarios" does not exist`**
→ Las tablas no se crearon. Ejecuta:
```powershell
python -c "from app import create_app, db; app=create_app('development'); app.app_context().push(); db.create_all()"
```

**Render/Heroku: la app no arranca**
→ Asegúrate de que `DATABASE_URL` en el dashboard de Render empiece con `postgresql://` (no `postgres://`). EduTrack ya lo arregla automáticamente, pero si la URL tiene otro problema, verifica que tu plan no haya expirado.
