"""
Tests de autenticación, seguridad y reset de contraseña.
"""
import pytest
from app.models import Usuario, IntentoLogin


class TestLogin:
    def test_login_get_devuelve_pagina(self, client):
        r = client.get('/auth/login')
        assert r.status_code == 200
        assert b'iniciar' in r.data.lower() or b'login' in r.data.lower()

    def test_login_correcto_redirige(self, client, admin_user):
        r = client.post('/auth/login', data={
            'username': 'testadmin', 'password': 'Test1234'
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_login_incorrecto_se_queda(self, client, admin_user):
        r = client.post('/auth/login', data={
            'username': 'testadmin', 'password': 'wrong'
        }, follow_redirects=False)
        # 200 = re-renderiza la página, no redirect
        assert r.status_code == 200

    def test_login_registra_intento_fallido(self, client, db, admin_user):
        client.post('/auth/login', data={
            'username': 'testadmin', 'password': 'wrong'
        })
        intentos = IntentoLogin.query.filter_by(exito=False).count()
        assert intentos >= 1

    def test_login_5_fallos_bloquea_cuenta(self, client, db, admin_user):
        for _ in range(5):
            client.post('/auth/login', data={
                'username': 'testadmin', 'password': 'wrong'
            })
        u = Usuario.query.filter_by(username='testadmin').first()
        assert u.intentos_fallidos >= 5
        assert u.esta_bloqueado() is True

    def test_login_exitoso_resetea_intentos(self, client, db, admin_user):
        # Primer fallo
        client.post('/auth/login', data={
            'username': 'testadmin', 'password': 'wrong'
        })
        # Login correcto
        client.post('/auth/login', data={
            'username': 'testadmin', 'password': 'Test1234'
        })
        u = Usuario.query.filter_by(username='testadmin').first()
        assert u.intentos_fallidos == 0


class TestPasswordValidator:
    def test_password_corta_rechazada(self):
        from app.utils.validators import validar_password
        valida, errs = validar_password('Ab1')
        assert valida is False
        assert any('8 caracteres' in e for e in errs)

    def test_password_sin_mayuscula_rechazada(self):
        from app.utils.validators import validar_password
        valida, _ = validar_password('abc12345xy')
        assert valida is False

    def test_password_comun_rechazada(self):
        from app.utils.validators import validar_password
        valida, _ = validar_password('admin123')
        assert valida is False

    def test_password_fuerte_aceptada(self):
        from app.utils.validators import validar_password
        valida, errs = validar_password('MiPass2026!')
        assert valida is True
        assert errs == []

    def test_password_contiene_username_rechazada(self):
        from app.utils.validators import validar_password
        valida, _ = validar_password('TestAdmin2026!', nombre_usuario='testadmin')
        assert valida is False


class TestResetPassword:
    def test_get_recuperar(self, client):
        r = client.get('/auth/recuperar')
        assert r.status_code == 200

    def test_post_email_valido_redirige(self, client, admin_user):
        r = client.post('/auth/recuperar', data={
            'email': 'admin@test.com'
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_post_email_invalido_mismo_redirect(self, client, admin_user):
        """Anti-enumeración: email inexistente debe dar mismo resultado."""
        r = client.post('/auth/recuperar', data={
            'email': 'noexiste@test.com'
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_token_valido_recupera_usuario(self, app, admin_user):
        with app.app_context():
            token = admin_user.generar_token_reset()
            u = Usuario.verificar_token_reset(token)
            assert u is not None
            assert u.id == admin_user.id

    def test_token_invalido_rechazado(self, app):
        with app.app_context():
            u = Usuario.verificar_token_reset('token-falso-no-firmado')
            assert u is None
