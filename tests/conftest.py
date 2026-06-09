"""
Configuración compartida de pytest.
Provee fixtures comunes: app, client, db, usuarios.
"""
import os
import sys
import pytest

# Asegurar que la app es importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db as _db
from app.models import Usuario, RolEnum


@pytest.fixture(scope='session')
def app():
    """Instancia única de la app en modo testing (BD en memoria)."""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['BCRYPT_LOG_ROUNDS'] = 4  # acelerar tests

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """BD limpia por cada test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        # Limpiar todas las tablas para el siguiente test
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    """Test client de Flask."""
    return app.test_client()


@pytest.fixture
def admin_user(db):
    """Crea un usuario admin de prueba."""
    u = Usuario(
        username='testadmin',
        email='admin@test.com',
        nombre_completo='Test Admin',
        rol=RolEnum.ADMIN.value,
        forzar_cambio_password=False,
    )
    u.set_password('Test1234')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def profesor_user(db):
    """Crea un usuario profesor de prueba."""
    u = Usuario(
        username='testprof',
        email='prof@test.com',
        nombre_completo='Test Profesor',
        rol=RolEnum.PROFESOR.value,
        forzar_cambio_password=False,
    )
    u.set_password('Test1234')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth_client(client, admin_user):
    """Cliente ya autenticado como admin."""
    client.post('/auth/login', data={
        'username': 'testadmin',
        'password': 'Test1234',
    }, follow_redirects=True)
    return client
