"""
Modelo de auditoría de intentos de login.
Registra cada intento (exitoso o fallido) para poder detectar
patrones sospechosos.
"""
from datetime import datetime
from app import db


class IntentoLogin(db.Model):
    __tablename__ = 'intentos_login'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    username_intentado = db.Column(db.String(120), nullable=False, index=True)
    ip = db.Column(db.String(45), nullable=True)  # IPv4 o IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    exito = db.Column(db.Boolean, default=False, nullable=False, index=True)
    motivo_fallo = db.Column(db.String(80), nullable=True)
    # Opciones de motivo_fallo: 'usuario_no_existe', 'password_incorrecta',
    # 'cuenta_inactiva', 'cuenta_bloqueada'

    def __repr__(self):
        estado = '✓' if self.exito else '✗'
        return f'<IntentoLogin {estado} {self.username_intentado} {self.timestamp}>'

    @staticmethod
    def registrar(username, ip, user_agent, exito, motivo_fallo=None):
        """Registra un intento. No falla si la BD tiene problemas (log-only)."""
        try:
            intento = IntentoLogin(
                username_intentado=(username or '')[:120],
                ip=(ip or '')[:45],
                user_agent=(user_agent or '')[:255],
                exito=exito,
                motivo_fallo=motivo_fallo,
            )
            db.session.add(intento)
            db.session.commit()
        except Exception:
            db.session.rollback()

    @staticmethod
    def intentos_fallidos_recientes(ip, minutos=15):
        """Cuántos intentos fallidos hay desde una IP en los últimos N minutos."""
        from datetime import timedelta
        desde = datetime.utcnow() - timedelta(minutes=minutos)
        return IntentoLogin.query.filter(
            IntentoLogin.ip == ip,
            IntentoLogin.exito == False,
            IntentoLogin.timestamp >= desde,
        ).count()
