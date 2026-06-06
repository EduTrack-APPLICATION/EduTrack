"""
Copia datos desde una base de datos SQLite hacia PostgreSQL.
Uso:
    python tools/sqlite_to_postgres.py /ruta/a/edutrack.db "postgresql://user:pass@host:port/dbname"

Requisitos:
    pip install sqlalchemy psycopg2-binary

Notas:
  - Asegúrate de ejecutar primero las migraciones en la DB de destino (flask db upgrade)
  - Este script asume que las tablas ya existen en PostgreSQL.
  - No maneja transformaciones complejas ni tipos especiales. Prueba en staging primero.
"""
import sys
import argparse
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.exc import SQLAlchemyError

CHUNK = 500


def copy_database(source_sqlite_path, target_url, echo=False):
    src_url = f'sqlite:///{source_sqlite_path}'
    src_engine = create_engine(src_url, echo=echo)
    tgt_engine = create_engine(target_url, echo=echo)

    src_meta = MetaData()
    tgt_meta = MetaData()

    print('Reflecting source (SQLite) metadata...')
    src_meta.reflect(bind=src_engine)
    print('Reflecting target (Postgres) metadata...')
    tgt_meta.reflect(bind=tgt_engine)

    # Verificar que el destino tenga las tablas
    missing = [t.name for t in src_meta.sorted_tables if t.name not in tgt_meta.tables]
    if missing:
        print('ERROR: Las siguientes tablas existen en SQLite pero faltan en PostgreSQL:')
        for m in missing:
            print('  -', m)
        print('\nEjecuta `flask db upgrade` en la base de datos de destino y vuelve a intentar.')
        return 2

    total_rows = 0
    with src_engine.connect() as src_conn, tgt_engine.connect() as tgt_conn:
        for table in src_meta.sorted_tables:
            table_name = table.name
            tgt_table = Table(table_name, tgt_meta, autoload_with=tgt_engine)
            print(f'Copiando tabla: {table_name} ...', end=' ')

            try:
                sel = select(table)
                result = src_conn.execute(sel)
            except SQLAlchemyError as e:
                print('ERROR al leer:', e)
                continue

            rows = result.fetchall()
            n = len(rows)
            if n == 0:
                print('0 filas')
                continue

            # Convert rows to list of dicts
            data = [dict(r._mapping) for r in rows]

            # Insert in chunks
            inserted = 0
            for i in range(0, len(data), CHUNK):
                chunk = data[i:i+CHUNK]
                try:
                    tgt_conn.execute(tgt_table.insert(), chunk)
                    inserted += len(chunk)
                except SQLAlchemyError as e:
                    print(f'\nERROR al insertar en {table_name}:', e)
                    return 3

            print(f'{inserted} filas')
            total_rows += inserted

    print(f'✓ Transferencia completa. Filas totales copiadas: {total_rows}')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copiar SQLite -> Postgres')
    parser.add_argument('sqlite_path', help='Ruta al archivo SQLite (.db)')
    parser.add_argument('postgres_url', help='URL de Postgres (postgresql://user:pass@host:port/dbname)')
    parser.add_argument('--echo', action='store_true', help='SQLAlchemy echo')
    args = parser.parse_args()

    sys.exit(copy_database(args.sqlite_path, args.postgres_url, echo=args.echo))
