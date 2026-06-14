"""
Application Factory para EduTrack.
Inicializa extensiones, registra blueprints y configura la app.
"""
import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

from config import config

# Extensiones (instanciadas sin app)
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()

# Configuración de login
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'
login_manager.session_protection = 'strong'


def create_app(config_name='default'):
    """Fábrica de la aplicación Flask."""
    app = Flask(__name__)

    print('=' * 50)
    print('DATABASE_URL:', os.getenv('DATABASE_URL'))
    print('=' * 50)

    if config_name == 'default' and not os.getenv('FLASK_ENV') and os.getenv('DATABASE_URL'):
        config_name = 'production'

    app.config.from_object(config[config_name])

    # Inicializar configuración adicional de entorno, si existe
    config_class = config.get(config_name)
    if config_class and hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # Loguear una versión segura de la URI de la base de datos
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url:
        safe_url = db_url
        if '://' in safe_url and '@' in safe_url:
            prefix, rest = safe_url.split('://', 1)
            if ':' in rest.split('@')[0]:
                user_part, host_part = rest.split('@', 1)
                user, _ = user_part.split(':', 1)
                safe_url = f'{prefix}://{user}:***@{host_part}'
        app.logger.info('Base de datos configurada en SQLALCHEMY_DATABASE_URI: %s', safe_url)

    # Inicializar extensiones
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)

    # === Seguridad: HTTPS + headers en producción ===
    if not app.debug and not app.testing:
        try:
            from flask_talisman import Talisman

            # Content Security Policy — permite los CDNs que usa la app
            csp = {
                'default-src': "'self'",
                'script-src': [
                    "'self'",
                    "'unsafe-inline'",  # necesario para inicialización inline de Chart.js
                    'https://cdn.jsdelivr.net',
                ],
                'style-src': [
                    "'self'",
                    "'unsafe-inline'",  # estilos inline usados en algunas plantillas
                    'https://cdn.jsdelivr.net',
                    'https://fonts.googleapis.com',
                ],
                'font-src': [
                    "'self'",
                    'https://fonts.gstatic.com',
                    'https://cdn.jsdelivr.net',
                    'data:',
                ],
                'img-src': ["'self'", 'data:', 'https:'],
                # Permitir conexiones al CDN para sourcemaps y recursos relacionados
                'connect-src': [
                    "'self'",
                    'https://cdn.jsdelivr.net',
                    'https://fonts.googleapis.com',
                    'https://fonts.gstatic.com',
                ],
                'frame-ancestors': "'none'",
                'base-uri': "'self'",
                'form-action': "'self'",
            }

            Talisman(
                app,
                force_https=app.config.get('FORCE_HTTPS', True),
                strict_transport_security=app.config.get(
                    'TALISMAN_STRICT_TRANSPORT_SECURITY', True),
                strict_transport_security_max_age=app.config.get(
                    'TALISMAN_STRICT_TRANSPORT_SECURITY_MAX_AGE', 31536000),
                content_security_policy=csp,
                content_security_policy_nonce_in=['script-src'],
                referrer_policy=app.config.get(
                    'TALISMAN_REFERRER_POLICY', 'strict-origin-when-cross-origin'),
                session_cookie_secure=True,
                session_cookie_http_only=True,
                frame_options='DENY',
            )
            app.logger.info('Flask-Talisman activado (HTTPS forzado + headers seguros)')
        except ImportError:
            app.logger.warning(
                'Flask-Talisman no está instalado. '
                'Instala con `pip install flask-talisman` para activar HTTPS y headers de seguridad.'
            )

    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.teachers import teachers_bp
    from app.routes.subjects import subjects_bp
    from app.routes.groups import groups_bp
    from app.routes.evaluations import evaluations_bp
    from app.routes.grades import grades_bp
    from app.routes.attendance import attendance_bp
    from app.routes.reports import reports_bp
    from app.routes.main import main_bp
    from app.routes.honor import honor_bp
    from app.routes.dev import dev_bp
    from app.routes.portal import portal_bp, redirect_if_estudiante

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(students_bp, url_prefix='/estudiantes')
    app.register_blueprint(teachers_bp, url_prefix='/profesores')
    app.register_blueprint(subjects_bp, url_prefix='/materias')
    app.register_blueprint(groups_bp, url_prefix='/grupos')
    app.register_blueprint(evaluations_bp, url_prefix='/evaluaciones')
    app.register_blueprint(grades_bp, url_prefix='/notas')
    app.register_blueprint(attendance_bp, url_prefix='/asistencia')
    app.register_blueprint(reports_bp, url_prefix='/reportes')
    app.register_blueprint(honor_bp, url_prefix='/cuadro-honor')
    app.register_blueprint(dev_bp, url_prefix='/dev')
    app.register_blueprint(portal_bp, url_prefix='/portal')

    # === Redirección automática para estudiantes ===
    # Si un estudiante intenta entrar a cualquier ruta fuera del portal → redirige
    @app.before_request
    def _redirect_estudiantes_al_portal():
        return redirect_if_estudiante()

    # === Modo mantenimiento ===
    @app.before_request
    def check_mantenimiento():
        # Permitir SIEMPRE: assets estáticos, login/logout, panel dev
        from flask import request
        if request.endpoint in ('static', 'auth.login', 'auth.logout', None):
            return
        if request.path.startswith('/static') or request.path.startswith('/dev'):
            return

        try:
            from app.models import Configuracion
            if Configuracion.get_bool('mantenimiento'):
                # Super_admins pasan, todos los demás ven la pantalla de mantenimiento
                if current_user.is_authenticated and current_user.is_super_admin():
                    return
                return render_template('errors/mantenimiento.html'), 503
        except Exception:
            # Si la tabla no existe aún (primer arranque), ignorar
            pass

    # Context processor: variables globales en todos los templates
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {'now': datetime.utcnow()}

    # Handlers de errores
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Filtros Jinja personalizados
    from app.utils.filters import register_filters
    register_filters(app)
   
    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import Usuario
    return Usuario.query.get(int(user_id))
