# EduTrack

Sistema de gestión académica web para colegios y escuelas. Permite gestionar estudiantes, profesores, materias, grupos, evaluaciones y asistencia, con generación automática de reportes y boletines.

---

## Tabla de contenidos

- [Características](#características)
- [Stack tecnológico](#stack-tecnológico)
- [Instalación rápida](#instalación-rápida)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Configuración](#configuración)
- [Uso](#uso)
- [Roles y permisos](#roles-y-permisos)
- [Seguridad](#seguridad)
- [Base de datos](#base-de-datos)
- [Email y reset de contraseña](#email-y-reset-de-contraseña)
- [Tests](#tests)
- [Despliegue en producción](#despliegue-en-producción)
- [Solución a problemas comunes](#solución-a-problemas-comunes)

---

## Características

### Gestión académica
- **Estudiantes** con código único, datos personales y contactos del encargado
- **Profesores** con asignación a materias específicas
- **Materias** con código, créditos y descripción
- **Grupos** que combinan materia + profesor + estudiantes matriculados
- **Evaluaciones** de varios tipos (examen, tarea, proyecto, quiz, práctica) con peso configurable
- **Asistencia** diaria con estados (presente, ausente, tarde, justificada)
- **Notas** con cálculo automático del promedio ponderado
- **Cuadro de honor** automático con generación de diplomas en PDF
- **Importador de Excel** con preview antes de confirmar

### Dashboard
- KPIs con tendencias (promedio, estudiantes, aprobación, asistencia)
- Sparklines SVG sin librerías pesadas
- Lista de estudiantes en riesgo académico
- Acciones rápidas contextuales
- Calendario de evaluaciones con FullCalendar
- Días feriados de Costa Rica marcados automáticamente

### Reportes
- Boletines individuales en PDF con diseño profesional
- Listas de calificaciones en Excel
- Reportes de asistencia
- Diplomas para el cuadro de honor (oro/plata/bronce)
- Generación masiva (próximamente)

### Seguridad
- Autenticación con bcrypt (12 rounds por defecto)
- **2FA TOTP** con códigos de recuperación (Google Authenticator, Authy, etc.)
- Reset de contraseña por email con tokens firmados y expiración
- Rate limiting por IP (10 fallos/15 min)
- Bloqueo automático de cuentas (5 fallos consecutivos → 15 min)
- Auditoría completa de intentos de login
- Política de contraseñas fuerte (8+ caracteres, mayús/minús/números, blocklist de comunes)
- Forzar cambio de contraseña en primer login
- CSRF protection (Flask-WTF)
- HTTPS forzado en producción (Flask-Talisman)
- Cookies HttpOnly + SameSite
- Anti-enumeración de usuarios en reset de contraseña

### UX
- Modo oscuro completo con paleta cuidada
- Diseño responsive con bottom navigation en mobile
- Tour guiado para nuevos usuarios
- Command Palette (Ctrl+K) para acciones rápidas
- Atajos de teclado con cheatsheet (?)
- Skeleton loading entre navegación
- Tooltips informativos
- Animaciones suaves entre tabs
- Avatares con iniciales coloreadas

### Mantenimiento
- **Papelera de reciclaje** (soft delete con retención de 30 días)
- **Panel del developer** para super_admins:
  - Diagnóstico del sistema
  - Estadísticas de BD por tabla
  - Errores capturados en memoria
  - Test de configuración SMTP
- **Feature flags** activables sin reiniciar:
  - Modo mantenimiento
  - Permitir importación masiva
  - Modo demo
  - Forzar 2FA en admins
- Acciones de mantenimiento (vaciar papelera, limpiar logs antiguos)

---

## Stack tecnológico

### Backend
- **Flask 3.x** — framework web
- **Flask-SQLAlchemy 3.x** — ORM
- **Flask-Login** — manejo de sesiones
- **Flask-Bcrypt** — hash de contraseñas
- **Flask-WTF** — formularios + CSRF
- **Flask-Migrate** — migraciones de BD
- **Flask-Mail** — envío de emails
- **Flask-Talisman** — headers de seguridad HTTP
- **pyotp + qrcode** — 2FA TOTP

### Frontend
- **Bootstrap 5.3** — base CSS
- **Bootstrap Icons** — iconografía
- **FullCalendar 6** — calendario interactivo
- **Inter font** — tipografía
- **JavaScript vanilla** — sin frameworks pesados (~1000 líneas)
- **SVG inline** para sparklines y empty states

### Reportes
- **ReportLab** — generación de PDFs
- **OpenPyXL** — generación de Excel

### Base de datos
- **SQLite** por defecto (cero configuración)
- **PostgreSQL** opcional (recomendado para producción)

---

## Instalación rápida

### Requisitos
- **Python 3.10+** (recomendado 3.12 o 3.13)
- **pip** (viene con Python)

### Setup en 4 pasos

```powershell
# 1. Clonar o descargar el proyecto
cd C:\ruta\donde\quieras\el\proyecto

# 2. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\Activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar e inicializar
python iniciar postgre.py
python setup.py
python run.py
```

El script `setup.py` automatiza:
- Verificación de Python 3.10+
- Creación del archivo `.env` con SECRET_KEY aleatoria
- Verificación de dependencias
- Creación de la base de datos
- Carga de datos demo (1 admin, 5 profesores, 30 estudiantes, evaluaciones, notas)

### Arrancar el servidor

```powershell
python run.py
```

Abre el navegador en **http://127.0.0.1:5000**

### Credenciales de prueba

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `developer` | `developer123` | Super Admin |
| `admin` | `admin123` | Administrador |
| `mrodriguez` | `profesor123` | Profesor |

> **Nota**: el sistema te forzará a cambiar la contraseña en el primer login por seguridad.

---

## Estructura del proyecto

```
EduTrack/
├── app/
│   ├── __init__.py           # Factory de la aplicación
│   ├── models/               # Modelos SQLAlchemy
│   │   ├── usuario.py        # User + roles + 2FA
│   │   ├── estudiante.py
│   │   ├── profesor.py
│   │   ├── materia.py
│   │   ├── grupo.py
│   │   ├── evaluacion.py
│   │   ├── nota.py
│   │   ├── asistencia.py
│   │   ├── intento_login.py  # Audit log
│   │   └── configuracion.py  # Feature flags
│   ├── routes/               # Blueprints
│   │   ├── auth.py           # Login, 2FA, reset password
│   │   ├── dashboard.py
│   │   ├── students.py
│   │   ├── teachers.py
│   │   ├── subjects.py
│   │   ├── groups.py
│   │   ├── evaluations.py    # Incluye calendario
│   │   ├── grades.py
│   │   ├── attendance.py
│   │   ├── reports.py
│   │   ├── honor.py
│   │   ├── dev.py            # Panel del developer
│   │   └── main.py           # API global
│   ├── services/             # Lógica de negocio
│   │   ├── calculo_service.py
│   │   ├── reporte_service.py
│   │   ├── importador_service.py
│   │   └── email_service.py
│   ├── templates/            # Jinja2 templates
│   ├── static/
│   │   ├── css/style.css     # ~6000 líneas
│   │   └── js/app.js         # ~1200 líneas
│   └── utils/
│       ├── decorators.py     # @admin_required, @super_admin_required
│       ├── forms.py          # WTForms
│       ├── validators.py     # Política de contraseñas
│       ├── filters.py        # Filtros Jinja2
│       └── seed_data.py      # Datos demo
├── tests/                    # pytest
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_estudiantes.py
│   ├── test_security_panel.py
│   └── test_calendario.py
├── migrations/               # Flask-Migrate
├── config.py                 # Configuración por entorno
├── run.py                    # Entry point
├── setup.py                  # Instalador interactivo
├── migrar.py                 # Migración SQLite → PostgreSQL
├── requirements.txt
├── .env.example
├── POSTGRESQL.md             # Guía de PostgreSQL
└── README.md                 # Este archivo
```

---

## Configuración

### Variables de entorno (`.env`)

Copia `.env.example` a `.env` y edita los valores:

```env
# Aplicación
FLASK_APP=run.py
FLASK_ENV=development
FLASK_CONFIG=development
SECRET_KEY=tu-clave-secreta-larga-y-aleatoria

# Base de datos (SQLite por defecto si se omite)
# DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/edutrack

# Bcrypt (12 para producción, 4 para dev rápido)
BCRYPT_LOG_ROUNDS=12

# Email (opcional — si no se configura, los emails van a la consola)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=true
# MAIL_USERNAME=tu-correo@gmail.com
# MAIL_PASSWORD=tu-app-password
# MAIL_DEFAULT_SENDER=tu-correo@gmail.com
```

---

## Uso

### Flujo típico de uso

1. **Login** con tu cuenta
2. **Cambiar contraseña** (forzado la primera vez)
3. **Activar 2FA** desde el menú de usuario (recomendado)
4. **Navegar** por el dashboard

### Crear una evaluación

1. Sidebar → **Evaluaciones** → **Nueva evaluación**
2. Completa: nombre, tipo, fecha, materia, grupo, porcentaje
3. Guardar

### Calificar

1. **Evaluaciones** → click en una evaluación → **Calificar**
2. Ingresa la nota de cada estudiante
3. Las notas se guardan automáticamente al cambiar de celda

### Importar estudiantes desde Excel

1. **Estudiantes** → **Importar Excel**
2. Descarga la plantilla, llénala
3. Sube el archivo → revisa el preview → confirma

### Generar boletín

1. **Reportes** → **Boletines**
2. Selecciona estudiante y período
3. Descarga el PDF

---

## Roles y permisos

| Rol | Acceso |
|-----|--------|
| **Super Admin** | Todo lo de Admin + Panel del developer + Feature flags |
| **Admin** | CRUD de profesores, configuración del sistema, todos los datos |
| **Profesor** | Solo sus grupos asignados, notas y asistencias de sus alumnos |

Los profesores que intentan acceder a recursos de otros profesores reciben **403 Forbidden**.

Para crear un super_admin adicional, inserta directamente en BD:

```sql
UPDATE usuarios SET rol = 'super_admin' WHERE username = 'tu_usuario';
```

---

## Seguridad

EduTrack implementa múltiples capas de seguridad:

### Autenticación
- Bcrypt con 12 rounds (configurable)
- 2FA TOTP opcional (códigos QR + recovery codes)
- Política de contraseñas: 8+ caracteres, mayús/minús/números, sin contraseñas comunes
- Bloqueo automático tras 5 intentos fallidos

### Protección contra ataques
- Rate limiting: 10 fallos por IP en 15 min
- CSRF tokens en todos los formularios (Flask-WTF)
- HTTPS forzado en producción (Flask-Talisman)
- Cookies HttpOnly + SameSite=Lax
- Anti-enumeración de usuarios en reset de contraseña

### Auditoría
- Todos los intentos de login quedan registrados con IP, user-agent, resultado
- Vista para admin en **Sistema → Auditoría de accesos**
- Detección de IPs sospechosas (>5 fallos/24h)

### Lo que NO está implementado (intencional)
- Acceso a contraseñas en texto plano (bcrypt es one-way)
- Login como otro usuario (impersonation)
- Ejecución de SQL arbitrario desde la UI

---

## Base de datos

### SQLite (default)
No requiere configuración. La BD se crea en `instance/edutrack.db` (o en la raíz como `edutrack.db`).

**Cuándo usarla:**
- Desarrollo
- Proyectos académicos
- < 20 usuarios simultáneos

### PostgreSQL (producción)
Ver [POSTGRESQL.md](./POSTGRESQL.md) para instrucciones completas.

**Resumen:**

1. Configura `DATABASE_URL` en `.env`:
   ```env
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/edutrack
   ```
2. Instala el driver: `pip install psycopg2-binary`
3. Ejecuta: `python setup.py`

**Migrar datos existentes de SQLite a PostgreSQL:**
```powershell
python migrar.py
```

### Papelera de reciclaje
Los estudiantes eliminados quedan con `eliminado_en = <timestamp>` por 30 días. Acceso en **Sistema → Papelera** (admin).

---

## Email y reset de contraseña

### Modo desarrollo (sin SMTP)
Por defecto, los emails se **imprimen en la consola del servidor**. Útil para probar el flujo sin configurar nada.

### Modo producción (con SMTP)

Configura las variables `MAIL_*` en `.env`. Servicios recomendados con tier gratis:

| Servicio | Cuota gratis | URL |
|----------|---------------|-----|
| **Brevo** (recomendado) | 300 emails/día | https://www.brevo.com/ |
| **Resend** | 100 emails/día | https://resend.com/ |
| **Mailtrap** (solo testing) | Bandeja virtual | https://mailtrap.io/ |

Ejemplo con Brevo:
```env
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-usuario-brevo
MAIL_PASSWORD=tu-smtp-key
MAIL_DEFAULT_SENDER=tu-correo@verificado.com
```

### Flujo de reset

1. Usuario va a `/auth/recuperar`
2. Ingresa su email
3. Mensaje genérico (anti-enumeración): "Si el correo existe, recibirás un enlace..."
4. Si el email existe, se envía un link firmado con expiración de 30 minutos
5. Click en el link → formulario de nueva contraseña → login automático

---

## Tests

EduTrack incluye **46 tests automatizados** con pytest.

### Ejecutar todos los tests

```powershell
pytest
```

### Ejecutar tests específicos

```powershell
pytest tests/test_auth.py              # Solo autenticación
pytest tests/test_calendario.py        # Solo calendario
pytest -k "test_login"                 # Por nombre
pytest -v                              # Verbose
pytest --tb=short                      # Tracebacks cortos
```

### Cobertura

```powershell
pip install pytest-cov
pytest --cov=app --cov-report=html
# Abre htmlcov/index.html
```

### Suites incluidas

- **test_auth.py** — Login, rate limiting, 2FA, recuperación
- **test_estudiantes.py** — CRUD + papelera (soft delete)
- **test_security_panel.py** — Roles, feature flags, modo mantenimiento
- **test_calendario.py** — API de eventos, reprogramar, feriados

Los tests usan SQLite en memoria + BCRYPT con 4 rounds → corren en ~20 segundos.

---

## Despliegue en producción

### Render (recomendado, gratis)

1. Push del proyecto a GitHub
2. En Render: **New +** → **Web Service** → conecta el repo
3. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
4. Variables de entorno en Render Dashboard:
   - `FLASK_CONFIG=production`
   - `SECRET_KEY=<genera-uno-aleatorio-largo>`
   - `DATABASE_URL=<de tu PostgreSQL en Render o Neon>`
   - `MAIL_*` si quieres email real
5. Deploy

### Railway

Similar a Render. Conecta GitHub, agrega un servicio PostgreSQL, define variables, deploy.

### VPS propio

```bash
# En tu servidor Ubuntu/Debian
sudo apt update && sudo apt install python3-pip python3-venv nginx
git clone <tu-repo> /opt/edutrack
cd /opt/edutrack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt psycopg2-binary
# Configura .env
python setup.py
# Corre con gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 run:app
# Configura nginx como reverse proxy con SSL (Let's Encrypt)
```

---

## Solución a problemas comunes

### `pip: not recognized` en PowerShell
El entorno virtual no está activado:
```powershell
.venv\Scripts\Activate
```

### Tour de bienvenida se queda pegado
F12 → Console → ejecuta:
```javascript
localStorage.setItem('edutrack-tour-completed-v1', '1');
location.reload();
```

### `password authentication failed` (PostgreSQL)
Verifica usuario, contraseña y nombre de BD en `DATABASE_URL`. El usuario debe tener permisos:
```sql
GRANT ALL ON SCHEMA public TO tu_usuario;
ALTER SCHEMA public OWNER TO tu_usuario;
```

### Setup se queda en "Cargando datos de prueba..."
Bcrypt es lento. Reduce los rounds en `.env`:
```env
BCRYPT_LOG_ROUNDS=4
```

### `No module named 'psycopg2'`
```powershell
pip install psycopg2-binary
```

### Email no llega
- Modo dev: revisa la consola del servidor, ahí imprime el email completo
- Modo producción: verifica las credenciales SMTP y que el remitente esté verificado en el servicio

### Recuperar contraseña del developer
Conéctate a la BD y resetea:
```sql
-- Bcrypt hash de "Developer2026!" (cambia después)
UPDATE usuarios SET
    password_hash = '$2b$12$tNvW8/Y7eP2qK0R6.G3eK.5fW0HsxRkP0vJqK0RfG3eK5fW0HsxRk',
    forzar_cambio_password = true,
    intentos_fallidos = 0,
    bloqueado_hasta = NULL
WHERE username = 'developer';
```

---

## Licencia

Proyecto académico. Uso libre con atribución.

## Créditos

Construido con Flask, Bootstrap, FullCalendar y mucho café.
