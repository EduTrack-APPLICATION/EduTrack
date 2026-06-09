"""
Modelo Usuario - autenticación y control de acceso.
"""
from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

from app import db, bcrypt


class RolEnum(str, Enum):
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    PROFESOR = 'profesor'
    ESTUDIANTE = 'estudiante'


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=RolEnum.PROFESOR.value)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    ultimo_login = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === Vínculo con Estudiante (para portal del estudiante) ===
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id', ondelete='SET NULL'),
                              nullable=True, index=True)

    # === Seguridad: bloqueo por intentos fallidos ===
    intentos_fallidos = db.Column(db.Integer, default=0, nullable=False)
    bloqueado_hasta = db.Column(db.DateTime, nullable=True)
    forzar_cambio_password = db.Column(db.Boolean, default=False, nullable=False)

    # === Seguridad: 2FA TOTP ===
    totp_secret = db.Column(db.String(32), nullable=True)
    totp_habilitado = db.Column(db.Boolean, default=False, nullable=False)
    recovery_codes_hash = db.Column(db.Text, nullable=True)  # JSON con hashes

    # Relaciones
    profesor = db.relationship('Profesor', backref='usuario', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self):
        # super_admin también tiene privilegios de admin
        return self.rol in (RolEnum.ADMIN.value, RolEnum.SUPER_ADMIN.value)

    def is_super_admin(self):
        return self.rol == RolEnum.SUPER_ADMIN.value

    def is_profesor(self):
        return self.rol == RolEnum.PROFESOR.value

    def is_estudiante(self):
        return self.rol == RolEnum.ESTUDIANTE.value

    # === Seguridad: bloqueo por intentos fallidos ===
    def esta_bloqueado(self):
        """Retorna True si la cuenta está temporalmente bloqueada."""
        if self.bloqueado_hasta is None:
            return False
        return datetime.utcnow() < self.bloqueado_hasta

    def minutos_bloqueado_restantes(self):
        """Minutos restantes de bloqueo (entero, mínimo 1)."""
        if not self.esta_bloqueado():
            return 0
        delta = self.bloqueado_hasta - datetime.utcnow()
        return max(1, int(delta.total_seconds() / 60) + 1)

    def registrar_intento_fallido(self, max_intentos=5, minutos_bloqueo=15):
        """Incrementa el contador y bloquea si llega al máximo."""
        self.intentos_fallidos = (self.intentos_fallidos or 0) + 1
        if self.intentos_fallidos >= max_intentos:
            from datetime import timedelta
            self.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=minutos_bloqueo)

    def resetear_intentos(self):
        """Resetea contador y bloqueo (tras login exitoso)."""
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None

    # === Seguridad: 2FA TOTP ===
    def generar_totp_secret(self):
        """Genera y guarda un nuevo secret TOTP. Aún no lo activa."""
        import pyotp
        self.totp_secret = pyotp.random_base32()
        return self.totp_secret

    def totp_uri(self):
        """URI para generar el QR code (formato otpauth://)."""
        import pyotp
        if not self.totp_secret:
            return None
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name='EduTrack'
        )

    def verificar_totp(self, codigo):
        """Verifica un código TOTP de 6 dígitos. Acepta ±1 ventana (~30s)."""
        import pyotp
        if not self.totp_secret:
            return False
        codigo = (codigo or '').strip().replace(' ', '')
        if not codigo.isdigit() or len(codigo) != 6:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(codigo, valid_window=1)

    def generar_recovery_codes(self, cantidad=10):
        """Genera N códigos de recuperación, los hashea y guarda. Retorna los códigos en claro (mostrar UNA vez)."""
        import secrets, json
        from flask_bcrypt import generate_password_hash
        codigos_claro = []
        hashes = []
        for _ in range(cantidad):
            # Formato: XXXX-XXXX (8 caracteres alfanuméricos)
            code = secrets.token_hex(4).upper()
            code_formatted = f'{code[:4]}-{code[4:]}'
            codigos_claro.append(code_formatted)
            hashes.append(generate_password_hash(code_formatted).decode('utf-8'))
        self.recovery_codes_hash = json.dumps(hashes)
        return codigos_claro

    def verificar_y_consumir_recovery_code(self, codigo):
        """Verifica un recovery code. Si es válido, lo consume (lo quita de la lista)."""
        import json
        from flask_bcrypt import check_password_hash
        if not self.recovery_codes_hash:
            return False
        codigo = (codigo or '').strip().upper()
        try:
            hashes = json.loads(self.recovery_codes_hash)
        except Exception:
            return False
        for i, h in enumerate(hashes):
            if check_password_hash(h, codigo):
                # Consumir: quitarlo de la lista
                hashes.pop(i)
                self.recovery_codes_hash = json.dumps(hashes)
                return True
        return False

    def recovery_codes_restantes(self):
        """Cuántos códigos de recuperación quedan."""
        import json
        if not self.recovery_codes_hash:
            return 0
        try:
            return len(json.loads(self.recovery_codes_hash))
        except Exception:
            return 0

    def generar_token_reset(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset')

    @staticmethod
    def verificar_token_reset(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='password-reset', max_age=expires_sec)
            return Usuario.query.get(data['user_id'])
        except Exception:
            return None

    def __repr__(self):
        return f'<Usuario {self.username} ({self.rol})>'
