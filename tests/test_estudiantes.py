"""
Tests del CRUD de estudiantes, papelera y dashboard.
"""
import pytest
from datetime import datetime
from app.models import Estudiante, EstadoEstudianteEnum


@pytest.fixture
def estudiante_demo(db):
    """Crea un estudiante de prueba."""
    e = Estudiante(
        codigo='EST-TEST001',
        nombre='María',
        apellido='Prueba',
        email='maria@test.com',
        estado=EstadoEstudianteEnum.ACTIVO.value,
    )
    db.session.add(e)
    db.session.commit()
    return e


class TestPapelera:
    def test_eliminar_no_borra_de_bd(self, auth_client, db, estudiante_demo):
        eid = estudiante_demo.id
        auth_client.post(f'/estudiantes/{eid}/eliminar')
        # Debe seguir en BD pero con eliminado_en
        e = db.session.get(Estudiante, eid)
        assert e is not None
        assert e.eliminado_en is not None

    def test_eliminado_no_aparece_en_listado(self, auth_client, db, estudiante_demo):
        eid = estudiante_demo.id
        codigo = estudiante_demo.codigo
        auth_client.post(f'/estudiantes/{eid}/eliminar')
        r = auth_client.get('/estudiantes/')
        assert codigo.encode() not in r.data

    def test_eliminado_aparece_en_papelera(self, auth_client, db, estudiante_demo):
        eid = estudiante_demo.id
        codigo = estudiante_demo.codigo
        auth_client.post(f'/estudiantes/{eid}/eliminar')
        r = auth_client.get('/estudiantes/papelera')
        assert r.status_code == 200
        assert codigo.encode() in r.data

    def test_restaurar_vuelve_a_lista(self, auth_client, db, estudiante_demo):
        eid = estudiante_demo.id
        auth_client.post(f'/estudiantes/{eid}/eliminar')
        auth_client.post(f'/estudiantes/{eid}/restaurar')
        e = db.session.get(Estudiante, eid)
        assert e.eliminado_en is None

    def test_eliminar_definitivo_borra_de_bd(self, auth_client, db, estudiante_demo):
        eid = estudiante_demo.id
        # Primero soft delete (requerido)
        auth_client.post(f'/estudiantes/{eid}/eliminar')
        # Ahora definitivo
        auth_client.post(f'/estudiantes/{eid}/eliminar-definitivo')
        e = db.session.get(Estudiante, eid)
        assert e is None


class TestRolesAccess:
    def test_admin_accede_a_profesores(self, auth_client):
        r = auth_client.get('/profesores/')
        assert r.status_code == 200

    def test_profesor_NO_accede_a_profesores(self, client, db, profesor_user):
        client.post('/auth/login', data={
            'username': 'testprof', 'password': 'Test1234'
        })
        r = client.get('/profesores/')
        assert r.status_code == 403

    def test_anonimo_redirigido_a_login(self, client):
        r = client.get('/dashboard/', follow_redirects=False)
        assert r.status_code in (302, 401)
        if r.status_code == 302:
            assert 'login' in r.location.lower()


class TestDashboard:
    def test_dashboard_carga(self, auth_client):
        r = auth_client.get('/dashboard/')
        assert r.status_code == 200

    def test_dashboard_tiene_kpis(self, auth_client):
        r = auth_client.get('/dashboard/')
        body = r.data.decode('utf-8')
        # Debe tener al menos los labels de los KPIs
        assert 'Promedio' in body or 'PROMEDIO' in body
        assert 'Estudiantes' in body or 'ESTUDIANTES' in body
