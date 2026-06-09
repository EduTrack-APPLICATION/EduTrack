"""
Migración manual: agrega la columna `estudiante_id` a la tabla `usuarios`
sin recrear ni perder datos.

Compatible con SQLite y PostgreSQL.

Uso:
    python migracion_portal.py
"""
from app import create_app, db
from sqlalchemy import text, inspect


def main():
    app = create_app('development')
    with app.app_context():
        inspector = inspect(db.engine)

        # Verificar si la columna ya existe
        columnas = [c['name'] for c in inspector.get_columns('usuarios')]
        if 'estudiante_id' in columnas:
            print('✓ La columna `estudiante_id` ya existe en `usuarios`. Nada que hacer.')
            return

        print('Agregando columna `estudiante_id` a la tabla `usuarios`...')
        try:
            with db.engine.connect() as conn:
                # SQLite y PostgreSQL aceptan esta sintaxis
                conn.execute(text(
                    'ALTER TABLE usuarios ADD COLUMN estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE SET NULL'
                ))
                conn.execute(text(
                    'CREATE INDEX IF NOT EXISTS ix_usuarios_estudiante_id ON usuarios(estudiante_id)'
                ))
                conn.commit()
            print('✓ Columna agregada correctamente.')
            print('  Índice creado: ix_usuarios_estudiante_id')
        except Exception as e:
            print(f'❌ Error: {e}')
            print('\nSi es PostgreSQL y dice "permission denied", asegúrate de que')
            print('tu usuario tenga ALTER en la tabla usuarios:')
            print('  GRANT ALL PRIVILEGES ON usuarios TO edutrack_user;')
            return

        print('\n✅ Migración completada. Ya puedes crear cuentas de estudiantes con:')
        print('   python crear_cuentas_estudiantes.py')


if __name__ == '__main__':
    main()
