"""
Rutas de autenticación: login, logout, recuperación de contraseña.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_

from app import db
from app.models import Usuario
from app.utils.forms import (
    LoginForm, ResetPasswordRequestForm, ResetPasswordForm, CambiarPasswordForm
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    from app.models import IntentoLogin

    # === Obtener IP y User-Agent ===
    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown'
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')[:255]

    form = LoginForm()
    if form.validate_on_submit():
        identificador = form.username.data.strip()

        # === Rate limiting por IP: máximo 10 intentos fallidos en 15 min ===
        fallos_recientes = IntentoLogin.intentos_fallidos_recientes(ip, minutos=15)
        if fallos_recientes >= 10:
            IntentoLogin.registrar(identificador, ip, user_agent,
                                    exito=False, motivo_fallo='rate_limit_ip')
            flash('Demasiados intentos fallidos desde tu conexión. '
                  'Espera 15 minutos antes de volver a intentar.', 'danger')
            return render_template('auth/login.html', form=form)

        user = Usuario.query.filter(
            or_(Usuario.username == identificador, Usuario.email == identificador)
        ).first()

        # === Verificar si la cuenta está bloqueada ===
        if user and user.esta_bloqueado():
            mins = user.minutos_bloqueado_restantes()
            IntentoLogin.registrar(identificador, ip, user_agent,
                                    exito=False, motivo_fallo='cuenta_bloqueada')
            flash(f'Cuenta bloqueada temporalmente por demasiados intentos. '
                  f'Intenta de nuevo en {mins} minuto{"s" if mins != 1 else ""}.',
                  'danger')
            return render_template('auth/login.html', form=form)

        if user and user.check_password(form.password.data):
            if not user.activo:
                IntentoLogin.registrar(identificador, ip, user_agent,
                                        exito=False, motivo_fallo='cuenta_inactiva')
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))

            # === Login exitoso (password OK) ===
            user.resetear_intentos()
            db.session.commit()

            # Si tiene 2FA habilitado, no loguear todavía: pedir código TOTP
            if user.totp_habilitado:
                # Guardar el ID del usuario en sesión temporal para el paso 2
                from flask import session
                session['pre_2fa_user_id'] = user.id
                session['pre_2fa_remember'] = form.remember.data
                session['pre_2fa_next'] = request.args.get('next')
                return redirect(url_for('auth.verificar_2fa'))

            # Sin 2FA: completar login inmediatamente
            user.ultimo_login = datetime.utcnow()
            db.session.commit()
            IntentoLogin.registrar(identificador, ip, user_agent, exito=True)

            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')

            # Si tiene contraseña por defecto, forzar cambio
            if user.forzar_cambio_password:
                flash('Por seguridad, debes cambiar tu contraseña antes de continuar.',
                      'warning')
                return redirect(url_for('auth.cambiar_password'))

            flash(f'Bienvenido(a), {user.nombre_completo}', 'success')
            return redirect(next_page or url_for('dashboard.index'))

        # === Login fallido ===
        if user:
            user.registrar_intento_fallido(max_intentos=5, minutos_bloqueo=15)
            db.session.commit()
            motivo = 'password_incorrecta'
            if user.esta_bloqueado():
                flash('Cuenta bloqueada por 15 minutos debido a múltiples intentos '
                      'fallidos.', 'danger')
            else:
                restantes = 5 - user.intentos_fallidos
                if restantes <= 2:
                    flash(f'Usuario o contraseña incorrectos. '
                          f'Te quedan {restantes} intento{"s" if restantes != 1 else ""} '
                          'antes de que la cuenta se bloquee.', 'danger')
                else:
                    flash('Usuario o contraseña incorrectos.', 'danger')
        else:
            motivo = 'usuario_no_existe'
            flash('Usuario o contraseña incorrectos.', 'danger')

        IntentoLogin.registrar(identificador, ip, user_agent,
                                exito=False, motivo_fallo=motivo)

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    from app.models import IntentoLogin
    from app.services.email_service import enviar_reset_password

    # IP para rate limiting + auditoría
    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown'
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')[:255]

    # Rate limit: máximo 5 solicitudes de reset desde la misma IP en 1 hora
    desde = datetime.utcnow() - timedelta(hours=1)
    intentos_recientes = IntentoLogin.query.filter(
        IntentoLogin.ip == ip,
        IntentoLogin.motivo_fallo == 'reset_password_solicitado',
        IntentoLogin.timestamp >= desde,
    ).count()

    form = ResetPasswordRequestForm()

    if intentos_recientes >= 5:
        flash('Has solicitado demasiados restablecimientos. Espera 1 hora '
              'antes de intentar de nuevo.', 'danger')
        return render_template('auth/recuperar.html', form=form)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = Usuario.query.filter_by(email=email).first()

        # Registrar el intento (sea exitoso o no) para auditoría
        IntentoLogin.registrar(
            email, ip, user_agent,
            exito=bool(user),
            motivo_fallo='reset_password_solicitado'
        )

        # SIEMPRE el mismo mensaje (anti-enumeración de usuarios)
        mensaje_publico = (
            'Si el correo está registrado, recibirás un enlace en los próximos '
            'minutos. Revisa también tu carpeta de spam.'
        )

        if user and user.activo:
            try:
                token = user.generar_token_reset()
                db.session.commit()
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                enviar_reset_password(user, reset_url)
            except Exception as e:
                current_app.logger.error(f'Error en flujo de reset: {e}')

        flash(mensaje_publico, 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/recuperar.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    user = Usuario.verificar_token_reset(token)
    if not user:
        flash('El enlace es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.recuperar_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Validar política de contraseñas
        from app.utils.validators import validar_password
        valida, errores = validar_password(
            form.password.data, user.username, user.email
        )
        if not valida:
            for err in errores:
                flash(err, 'danger')
            return render_template('auth/reset.html', form=form)

        user.set_password(form.password.data)
        user.resetear_intentos()
        user.forzar_cambio_password = False
        db.session.commit()
        flash('Contraseña actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset.html', form=form)


@auth_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    form = CambiarPasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password_actual.data):
            flash('Contraseña actual incorrecta.', 'danger')
        else:
            # Validar política de contraseñas
            from app.utils.validators import validar_password
            valida, errores = validar_password(
                form.password_nueva.data,
                current_user.username, current_user.email
            )
            if not valida:
                for err in errores:
                    flash(err, 'danger')
            elif form.password_nueva.data == form.password_actual.data:
                flash('La nueva contraseña debe ser diferente a la actual.', 'danger')
            else:
                current_user.set_password(form.password_nueva.data)
                current_user.forzar_cambio_password = False
                db.session.commit()
                flash('Contraseña actualizada correctamente.', 'success')
                return redirect(url_for('dashboard.index'))
    return render_template('auth/cambiar_password.html', form=form)


# === Vista de auditoría de intentos de login (solo admin) ===
@auth_bp.route('/auditoria/intentos-login')
@login_required
def auditoria_intentos():
    """Muestra los últimos 100 intentos de login."""
    if not current_user.is_admin():
        flash('Solo administradores pueden acceder a la auditoría.', 'danger')
        return redirect(url_for('dashboard.index'))

    from app.models import IntentoLogin
    from sqlalchemy import desc, func

    intentos = IntentoLogin.query.order_by(
        desc(IntentoLogin.timestamp)
    ).limit(100).all()

    # Estadísticas rápidas
    from datetime import timedelta
    desde_24h = datetime.utcnow() - timedelta(hours=24)
    total_24h = IntentoLogin.query.filter(IntentoLogin.timestamp >= desde_24h).count()
    fallos_24h = IntentoLogin.query.filter(
        IntentoLogin.timestamp >= desde_24h,
        IntentoLogin.exito == False
    ).count()

    # IPs sospechosas (>5 fallos en 24h)
    ips_sospechosas = db.session.query(
        IntentoLogin.ip, func.count(IntentoLogin.id).label('fallos')
    ).filter(
        IntentoLogin.timestamp >= desde_24h,
        IntentoLogin.exito == False,
    ).group_by(IntentoLogin.ip).having(
        func.count(IntentoLogin.id) > 5
    ).all()

    return render_template(
        'auth/auditoria.html',
        intentos=intentos,
        total_24h=total_24h,
        fallos_24h=fallos_24h,
        ips_sospechosas=ips_sospechosas,
    )


# ============================================================
# 2FA TOTP — verificación, setup, deshabilitar
# ============================================================

@auth_bp.route('/verificar-2fa', methods=['GET', 'POST'])
def verificar_2fa():
    """Paso 2 del login: pide el código TOTP."""
    from flask import session
    from app.models import IntentoLogin

    user_id = session.get('pre_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = Usuario.query.get(user_id)
    if not user:
        session.pop('pre_2fa_user_id', None)
        return redirect(url_for('auth.login'))

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown'
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')[:255]

    if request.method == 'POST':
        codigo = (request.form.get('codigo') or '').strip()
        usar_recovery = request.form.get('recovery') == '1'

        verificado = False
        es_recovery = False

        if usar_recovery:
            if user.verificar_y_consumir_recovery_code(codigo):
                verificado = True
                es_recovery = True
                db.session.commit()
        else:
            if user.verificar_totp(codigo):
                verificado = True

        if verificado:
            user.ultimo_login = datetime.utcnow()
            db.session.commit()
            IntentoLogin.registrar(user.username, ip, user_agent, exito=True)

            remember = session.pop('pre_2fa_remember', False)
            next_page = session.pop('pre_2fa_next', None)
            session.pop('pre_2fa_user_id', None)

            login_user(user, remember=remember)

            if es_recovery:
                restantes = user.recovery_codes_restantes()
                flash(f'Código de recuperación usado correctamente. '
                      f'Te quedan {restantes}.', 'warning')
            else:
                flash(f'Bienvenido(a), {user.nombre_completo}', 'success')

            if user.forzar_cambio_password:
                return redirect(url_for('auth.cambiar_password'))

            return redirect(next_page or url_for('dashboard.index'))

        # Código incorrecto
        IntentoLogin.registrar(user.username, ip, user_agent,
                                exito=False, motivo_fallo='2fa_incorrecto')
        flash('Código incorrecto. Verifica el código en tu app de autenticación.',
              'danger')

    return render_template('auth/verificar_2fa.html',
                           username=user.username,
                           recovery_restantes=user.recovery_codes_restantes())


@auth_bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Configurar 2FA para la cuenta del usuario actual."""
    import io, base64
    import qrcode

    if current_user.totp_habilitado:
        flash('El 2FA ya está habilitado en tu cuenta.', 'info')
        return redirect(url_for('auth.config_2fa'))

    # Generar secret si no existe (o si se descartó uno previo no confirmado)
    if not current_user.totp_secret:
        current_user.generar_totp_secret()
        db.session.commit()

    if request.method == 'POST':
        codigo = (request.form.get('codigo') or '').strip()
        if current_user.verificar_totp(codigo):
            current_user.totp_habilitado = True
            codigos = current_user.generar_recovery_codes(10)
            db.session.commit()
            flash('¡2FA activado correctamente! Guarda tus códigos de recuperación.',
                  'success')
            return render_template('auth/recovery_codes.html',
                                   codigos=codigos, primera_vez=True)
        flash('Código incorrecto. Verifica e intenta de nuevo.', 'danger')

    # Generar QR code
    uri = current_user.totp_uri()
    qr_img = qrcode.make(uri, box_size=8, border=2)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    qr_data = base64.b64encode(buf.getvalue()).decode('ascii')

    return render_template('auth/setup_2fa.html',
                           qr_data=qr_data,
                           secret=current_user.totp_secret)


@auth_bp.route('/2fa/config')
@login_required
def config_2fa():
    """Página de configuración del 2FA (estado, opciones)."""
    return render_template('auth/config_2fa.html',
                           recovery_restantes=current_user.recovery_codes_restantes())


@auth_bp.route('/2fa/deshabilitar', methods=['POST'])
@login_required
def deshabilitar_2fa():
    """Deshabilita el 2FA. Requiere contraseña actual."""
    password = request.form.get('password', '')
    if not current_user.check_password(password):
        flash('Contraseña incorrecta. No se realizó ningún cambio.', 'danger')
        return redirect(url_for('auth.config_2fa'))

    current_user.totp_habilitado = False
    current_user.totp_secret = None
    current_user.recovery_codes_hash = None
    db.session.commit()
    flash('2FA deshabilitado.', 'info')
    return redirect(url_for('auth.config_2fa'))


@auth_bp.route('/2fa/regenerar-codigos', methods=['POST'])
@login_required
def regenerar_recovery_codes():
    """Genera 10 nuevos códigos de recuperación. Los anteriores quedan inválidos."""
    if not current_user.totp_habilitado:
        flash('Primero debes activar el 2FA.', 'warning')
        return redirect(url_for('auth.config_2fa'))

    password = request.form.get('password', '')
    if not current_user.check_password(password):
        flash('Contraseña incorrecta. No se generaron nuevos códigos.', 'danger')
        return redirect(url_for('auth.config_2fa'))

    codigos = current_user.generar_recovery_codes(10)
    db.session.commit()
    flash('Nuevos códigos generados. Los anteriores ya no funcionan.', 'success')
    return render_template('auth/recovery_codes.html',
                           codigos=codigos, primera_vez=False)
