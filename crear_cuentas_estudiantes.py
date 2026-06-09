"""
Genera cuentas del portal para estudiantes (lote).

Uso:
    python crear_cuentas_estudiantes.py            # crea para todos los que no tienen
    python crear_cuentas_estudiantes.py --id 5     # solo para id=5
    python crear_cuentas_estudiantes.py --reset 5  # resetea la contraseña del id=5
"""
import sys
from app import create_app
from app.models import Usuario, Estudiante
from app.utils.portal_helpers import generar_cuenta_estudiante


def _print_credenciales(est, cuenta):
    accion = 'RESET' if cuenta['reset'] else 'CREADA'
    print(f'  ✓ {accion} {est.codigo} ({est.nombre_completo})')
    print(f'      Usuario:    {cuenta["username"]}')
    print(f'      Contraseña: {cuenta["password"]}')
    print(f'      Email:      {cuenta["usuario"].email}')


def main():
    args = sys.argv[1:]
    target_id = None
    reset = False
    if '--id' in args:
        target_id = int(args[args.index('--id') + 1])
    if '--reset' in args:
        target_id = int(args[args.index('--reset') + 1])
        reset = True

    app = create_app('development')
    with app.app_context():
        if target_id:
            est = Estudiante.query.get(target_id)
            if not est:
                print(f'❌ Estudiante con id={target_id} no existe')
                sys.exit(1)
            cuenta = generar_cuenta_estudiante(est, reset=reset)
            if cuenta is None:
                print(f'⚠ {est.codigo} ya tiene cuenta. Usa --reset para regenerar.')
            else:
                _print_credenciales(est, cuenta)
        else:
            estudiantes = Estudiante.query.filter(Estudiante.eliminado_en.is_(None)).all()
            sin_cuenta = [e for e in estudiantes
                          if not Usuario.query.filter_by(estudiante_id=e.id).first()]
            if not sin_cuenta:
                print('✓ Todos los estudiantes activos ya tienen cuenta.')
                return
            print(f'\nCreando cuentas para {len(sin_cuenta)} estudiante(s)...\n')
            for e in sin_cuenta:
                cuenta = generar_cuenta_estudiante(e)
                if cuenta:
                    _print_credenciales(e, cuenta)
            print(f'\n✅ {len(sin_cuenta)} cuentas creadas.')


if __name__ == '__main__':
    main()
