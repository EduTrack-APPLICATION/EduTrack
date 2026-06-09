"""
Tests del panel del developer, feature flags y calendario.
"""
import pytest
from app.models import Usuario, RolEnum, Configuracion, Evaluacion


@pytest.fixture
def super_admin(db):
    u = Usuario(
        username='testdev',
        email='dev@test.com',
        nombre_completo='Test Developer',
        rol=RolEnum.SUPER_ADMIN.value,
        forzar_cambio_password=False,
    )
    u.set_password('Test1234')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def dev_client(client, super_admin):
    client.post('/auth/login', data={
        'username': 'testdev', 'password': 'Test1234'
    })
    return client


class TestDevPanel:
    def test_admin_normal_NO_ve_dev_panel(self, auth_client):
        """El admin normal recibe 404 (oculto), no 403."""
        r = auth_client.get('/dev/')
        assert r.status_code == 404

    def test_super_admin_accede_a_dev(self, dev_client):
        r = dev_client.get('/dev/')
        assert r.status_code == 200
        assert b'Panel del desarrollador' in r.data

    def test_anonimo_NO_accede_a_dev(self, client):
        r = client.get('/dev/', follow_redirects=False)
        assert r.status_code in (302, 401)


class TestFeatureFlags:
    def test_get_flag_default(self, app, db):
        with app.app_context():
            valor = Configuracion.get_bool('mantenimiento')
            assert valor is False

    def test_set_flag_persiste(self, app, db):
        with app.app_context():
            Configuracion.set('mantenimiento', 'true')
            valor = Configuracion.get_bool('mantenimiento')
            assert valor is True

    def test_toggle_via_endpoint(self, dev_client, db):
        # Toggle ON
        dev_client.post('/dev/feature-flags', data={'clave': 'modo_demo'})
        valor = Configuracion.get_bool('modo_demo')
        assert valor is True
        # Toggle OFF
        dev_client.post('/dev/feature-flags', data={'clave': 'modo_demo'})
        valor = Configuracion.get_bool('modo_demo')
        assert valor is False

    def test_flag_invalido_rechazado(self, dev_client):
        r = dev_client.post('/dev/feature-flags',
                             data={'clave': 'flag_no_existe'})
        # Redirige con flash de error, no crashea
        assert r.status_code in (302, 200)


class TestMantenimiento:
    def test_modo_activo_bloquea_usuarios(self, app, db, client, admin_user):
        """Con mantenimiento ON, un admin normal ve la página de mantenimiento."""
        with app.app_context():
            Configuracion.set('mantenimiento', 'true')

        client.post('/auth/login', data={
            'username': 'testadmin', 'password': 'Test1234'
        })
        r = client.get('/dashboard/')
        assert r.status_code == 503
        assert b'Volveremos' in r.data or b'mantenimiento' in r.data.lower()

        # Apagar
        with app.app_context():
            Configuracion.set('mantenimiento', 'false')

    def test_super_admin_pasa_mantenimiento(self, app, db, dev_client):
        with app.app_context():
            Configuracion.set('mantenimiento', 'true')

        r = dev_client.get('/dashboard/')
        assert r.status_code == 200

        with app.app_context():
            Configuracion.set('mantenimiento', 'false')
