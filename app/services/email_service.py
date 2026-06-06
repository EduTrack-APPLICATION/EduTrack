"""
Servicio de envío de emails.

Si MAIL_USERNAME y MAIL_PASSWORD están configurados (.env), envía vía SMTP real.
Si no, imprime el contenido en la consola del servidor (modo desarrollo).

Esto permite probar el flujo de reset de contraseña sin configurar SMTP.
"""
import threading
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail


# ============================================================
# Plantilla HTML del email de reset de contraseña
# ============================================================
RESET_PASSWORD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Restablece tu contraseña</title>
</head>
<body style="margin:0; padding:0; background:#f1f5f9; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; color:#0f172a;">
  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#f1f5f9; padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:560px; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(15,23,42,0.06);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg, #1e40af 0%, #6366f1 100%); padding:32px 32px 28px; text-align:center;">
              <div style="display:inline-block; width:56px; height:56px; line-height:56px; border-radius:14px; background:rgba(255,255,255,0.18); color:#ffffff; font-size:28px; margin-bottom:12px;">🔐</div>
              <h1 style="margin:0; color:#ffffff; font-size:22px; font-weight:700; letter-spacing:-0.02em;">EduTrack</h1>
              <p style="margin:4px 0 0; color:rgba(255,255,255,0.85); font-size:13px;">Sistema académico</p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 32px 16px;">
              <h2 style="margin:0 0 16px; font-size:20px; font-weight:700; color:#0f172a;">Hola, {{ nombre }}</h2>
              <p style="margin:0 0 16px; font-size:15px; line-height:1.55; color:#475569;">
                Recibimos una solicitud para restablecer la contraseña de tu cuenta en EduTrack.
                Haz clic en el botón a continuación para crear una nueva contraseña.
              </p>

              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:24px auto;">
                <tr>
                  <td align="center" style="border-radius:8px; background:#1e40af;">
                    <a href="{{ reset_url }}"
                       style="display:inline-block; padding:14px 28px; font-size:15px; font-weight:600; color:#ffffff; text-decoration:none; border-radius:8px;">
                      Restablecer contraseña
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:24px 0 8px; font-size:13px; color:#64748b;">
                ¿No funciona el botón? Copia y pega este enlace en tu navegador:
              </p>
              <p style="margin:0 0 16px; padding:12px 14px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-size:12px; color:#334155; word-break:break-all; font-family:monospace;">
                {{ reset_url }}
              </p>

              <!-- Security note -->
              <div style="margin-top:24px; padding:14px 16px; background:#fef3c7; border-left:3px solid #f59e0b; border-radius:4px;">
                <p style="margin:0 0 4px; font-size:13px; font-weight:600; color:#78350f;">⚠ Importante</p>
                <p style="margin:0; font-size:13px; line-height:1.5; color:#92400e;">
                  Este enlace expira en <strong>30 minutos</strong>. Si no solicitaste este cambio,
                  ignora este mensaje — tu contraseña permanecerá segura.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:16px 32px 32px; border-top:1px solid #e2e8f0;">
              <p style="margin:0; font-size:12px; color:#94a3b8; text-align:center; line-height:1.5;">
                Este correo fue enviado a <strong>{{ email }}</strong>.<br>
                Si necesitas ayuda, contacta al administrador del sistema.
              </p>
              <p style="margin:8px 0 0; font-size:11px; color:#cbd5e1; text-align:center;">
                © 2026 EduTrack · No responder a este correo
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()


# Versión texto plano (fallback para clientes que no leen HTML)
RESET_PASSWORD_TEXT = """
EduTrack — Restablecimiento de contraseña

Hola, {nombre}.

Recibimos una solicitud para restablecer la contraseña de tu cuenta en EduTrack.

Para crear una nueva contraseña, visita el siguiente enlace:

{reset_url}

⚠ Este enlace expira en 30 minutos.

Si no solicitaste este cambio, ignora este mensaje — tu contraseña permanecerá segura.

---
Este correo fue enviado a {email}.
© 2026 EduTrack
""".strip()


def _enviar_async(app, msg):
    """Envío en thread separado para no bloquear la petición HTTP."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f'Error enviando email: {e}')


def enviar_email(to, subject, html, text=None):
    """
    Envía un email. Si MAIL no está configurado, loggea a consola.
    El envío real ocurre en un thread aparte (no bloquea).
    """
    if not current_app.config.get('MAIL_ENABLED'):
        # Modo desarrollo: imprimir en consola
        current_app.logger.info('=' * 70)
        current_app.logger.info('📧 EMAIL (modo desarrollo — no se envió por SMTP)')
        current_app.logger.info(f'  Para:     {to}')
        current_app.logger.info(f'  Asunto:   {subject}')
        if text:
            current_app.logger.info('  Contenido:')
            for line in text.split('\n'):
                current_app.logger.info(f'    {line}')
        current_app.logger.info('=' * 70)
        return True

    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=html,
            body=text,
        )
        # Envío asíncrono
        app = current_app._get_current_object()
        thread = threading.Thread(target=_enviar_async, args=(app, msg))
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        current_app.logger.error(f'No se pudo preparar email: {e}')
        return False


def enviar_reset_password(usuario, reset_url):
    """Envía el email de reset de contraseña."""
    html = render_template_string(
        RESET_PASSWORD_HTML,
        nombre=usuario.nombre_completo,
        email=usuario.email,
        reset_url=reset_url,
    )
    text = RESET_PASSWORD_TEXT.format(
        nombre=usuario.nombre_completo,
        email=usuario.email,
        reset_url=reset_url,
    )
    return enviar_email(
        to=usuario.email,
        subject='Restablece tu contraseña en EduTrack',
        html=html,
        text=text,
    )
