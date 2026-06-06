"""
Modelo de configuración del sistema (feature flags).
Tabla key-value simple para almacenar settings que se pueden cambiar
en runtime desde el panel de desarrollador.
"""
from datetime import datetime
from app import db


class Configuracion(db.Model):
    __tablename__ = 'configuracion'

    clave = db.Column(db.String(80), primary_key=True)
    valor = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    # Defaults conocidos
    DEFAULTS = {
        'mantenimiento':         ('false', 'Modo mantenimiento (app inaccesible)'),
        'permitir_importacion':  ('true',  'Permitir importación masiva de Excel'),
        'modo_demo':             ('false', 'Modo demo (cambios no se persisten)'),
        'forzar_2fa_admin':      ('false', 'Forzar 2FA en cuentas admin'),
    }

    @staticmethod
    def get(clave, default=None):
        """Lee un valor. Si no existe, retorna el default."""
        c = Configuracion.query.get(clave)
        if c:
            return c.valor
        if clave in Configuracion.DEFAULTS:
            return Configuracion.DEFAULTS[clave][0]
        return default

    @staticmethod
    def get_bool(clave, default=False):
        """Lee un valor como booleano."""
        v = Configuracion.get(clave)
        if v is None:
            return default
        return str(v).lower() in ('true', '1', 'yes', 'on')

    @staticmethod
    def set(clave, valor, descripcion=None):
        """Establece un valor."""
        c = Configuracion.query.get(clave)
        if c:
            c.valor = str(valor)
            if descripcion:
                c.descripcion = descripcion
        else:
            c = Configuracion(
                clave=clave,
                valor=str(valor),
                descripcion=descripcion or Configuracion.DEFAULTS.get(clave, ('', ''))[1],
            )
            db.session.add(c)
        db.session.commit()
        return c

    @staticmethod
    def all_flags():
        """Retorna todos los flags conocidos con su valor actual."""
        result = []
        for clave, (default_val, desc) in Configuracion.DEFAULTS.items():
            valor = Configuracion.get(clave, default_val)
            result.append({
                'clave': clave,
                'valor': str(valor).lower() in ('true', '1', 'yes', 'on'),
                'descripcion': desc,
            })
        return result
