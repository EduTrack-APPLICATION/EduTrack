"""
Configuración de la aplicación EduTrack.
Soporta entornos de desarrollo, testing y producción.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))



def _fix_database_url(url):
    """
    Heroku/Render entregan 'postgres://' pero SQLAlchemy 2.x exige 'postgresql://'.
    También permite especificar el driver psycopg2 explícitamente.
    """
    if not url:
        return url
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    """Configuración base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'edutrack-super-secret-key-change-in-production-2026'

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,   # detecta conexiones muertas
        'pool_recycle': 300,     # recicla cada 5 min
        'pool_size': 10,
        'max_overflow': 20,
    }

    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY = True

    # Bcrypt
    BCRYPT_LOG_ROUNDS = 12

    # Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')

    # Paginación
    ITEMS_PER_PAGE = 20

    # Reglas académicas
    NOTA_MINIMA_APROBACION = 70.0
    NOTA_RECUPERACION = 60.0
    ASISTENCIA_MINIMA = 80.0

    # === Email (Flask-Mail) ===
    # Configura via .env. Si no hay credenciales, los emails se imprimen en consola.
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', '1', 'yes')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or \
        os.environ.get('MAIL_USERNAME') or 'no-reply@edutrack.local'
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ('true', '1')
    # Si no hay USERNAME/PASSWORD, se loggea a consola en lugar de enviar
    MAIL_ENABLED = bool(MAIL_USERNAME and MAIL_PASSWORD)


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLite por defecto — no requiere instalación adicional.
    # Para usar PostgreSQL, define DATABASE_URL en .env
    SQLALCHEMY_DATABASE_URI = _fix_database_url(os.environ.get('DATABASE_URL')) or \
        'sqlite:///' + os.path.join(basedir, 'edutrack.db')
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _fix_database_url(os.environ.get('TEST_DATABASE_URL')) or \
        'sqlite:///' + os.path.join(basedir, 'test.db')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _fix_database_url(os.environ.get('DATABASE_URL'))

    # === Seguridad de cookies ===
    SESSION_COOKIE_SECURE = True       # solo HTTPS
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # === HTTPS / Headers (Flask-Talisman) ===
    # Si la app corre detrás de un proxy/load-balancer que ya termina SSL,
    # se puede desactivar el force_https desde el .env.
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'true').lower() in ('true', '1', 'yes')
    TALISMAN_STRICT_TRANSPORT_SECURITY = True
    TALISMAN_STRICT_TRANSPORT_SECURITY_MAX_AGE = 31536000  # 1 año
    TALISMAN_REFERRER_POLICY = 'strict-origin-when-cross-origin'

    @classmethod
    def init_app(cls, app):
        # Validar variables críticas en producción
        assert cls.SQLALCHEMY_DATABASE_URI, 'DATABASE_URL debe estar configurada en producción'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
