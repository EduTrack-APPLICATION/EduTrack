# EduTrack

Sistema de Gestión Académica para instituciones educativas de Costa Rica.
EduTrack centraliza la gestión de estudiantes, profesores, materias, grupos, evaluaciones, asistencia y reportes en una plataforma web moderna, segura y accesible desde cualquier dispositivo.

**Sitio en producción**: [www.edu-track.school](https://www.edu-track.school)

---

## Tabla de contenidos

1. [Tecnologías](#tecnologías)
2. [Arquitectura](#arquitectura)
3. [Funcionalidades implementadas](#funcionalidades-implementadas)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Instalación local](#instalación-local)
6. [Configuración del servidor de correos](#configuración-del-servidor-de-correos-brevo)
7. [Despliegue en producción](#despliegue-en-producción)
8. [Credenciales por defecto](#credenciales-por-defecto)
9. [Bugs conocidos](#bugs-conocidos)
10. [Pendientes y mejoras futuras](#pendientes-y-mejoras-futuras)
11. [Autores](#autores)

---

## Tecnologías

### Backend
- **Python 3.11+**
- **Flask 3.0** — framework web
- **SQLAlchemy 2.0** — ORM
- **PostgreSQL** — base de datos (producción)
- **SQLite** — base de datos (desarrollo local)
- **Flask-Login** — gestión de sesiones
- **Flask-Bcrypt** — hash de contraseñas
- **Flask-WTF** — formularios y CSRF
- **Flask-Migrate** — migraciones de BD
- **Flask-Talisman** — headers de seguridad y HTTPS
- **Flask-Mail** — envío de correos
- **PyOTP + qrcode** — verificación en dos pasos (TOTP)

### Frontend
- **Bootstrap 5.3** — sistema de componentes base
- **Inter (Google Fonts)** — tipografía principal
- **Bootstrap Icons** — iconos
- **CSS custom** con efectos liquid glass
- **JavaScript vanilla** (sin frameworks)

### Infraestructura
- **Render** — hosting del backend Flask + PostgreSQL
- **Cloudflare** — DNS y proxy del dominio
- **Brevo (ex-Sendinblue)** — SMTP para correos transaccionales

---

## Arquitectura

```
Usuario navegador
      |
      v
Cloudflare DNS (edu-track.school)
      |
      v
Render Web Service (Flask 3 + Gunicorn)
      |
      +--> PostgreSQL (Render Managed)
      |
      +--> Brevo SMTP (correos de activación, recuperación)
      |
      +--> Almacenamiento estático (Flask static)
```

El sistema está organizado siguiendo el patrón **application factory** de Flask, con blueprints separados por dominio funcional.

---

## Funcionalidades implementadas

### Autenticación y seguridad

- Login con username, email o cédula
- Recuperación de contraseña por correo (token con expiración de 48 horas)
- Verificación en dos pasos (TOTP compatible con Google Authenticator, Authy, Microsoft Authenticator)
- Códigos de recuperación de 2FA (10 códigos generados al activar, cada uno de un solo uso)
- Cambio obligatorio de contraseña en primer inicio de sesión
- Rate limiting de intentos fallidos por IP y usuario
- Bloqueo temporal de cuenta después de 5 intentos fallidos
- Auditoría de intentos de acceso (exitosos y fallidos) con IP y user-agent
- Activación de cuenta por link enviado por correo
- HTTPS obligatorio en producción
- Content Security Policy (CSP) configurado
- Cookies seguras (HttpOnly, Secure, SameSite)

### Roles del sistema

- **SUPER_ADMIN** — control total del sistema, acceso al panel de developer
- **ADMIN** — gestión completa de estudiantes, profesores, materias, grupos
- **PROFESOR** — gestión de sus propios grupos, evaluaciones, calificaciones y asistencia
- **ESTUDIANTE** — acceso de solo lectura al portal estudiantil con sus datos

### Gestión académica

- CRUD completo de estudiantes con código estudiantil, cédula, encargado, sección
- CRUD completo de profesores con asignación de materias
- CRUD completo de materias con código, créditos y horas semanales
- CRUD completo de grupos con periodo, año, cupo, aula y horario
- Matrícula de estudiantes en grupos
- Asignación de materias a profesores

### Evaluaciones y calificaciones

- Creación de evaluaciones con 7 tipos: examen, quiz, tarea, proyecto, exposición, práctica, participación
- Configuración de puntaje máximo y porcentaje de la nota final
- Calificación individual o por lote
- Cálculo automático de promedios ponderados
- Observaciones del profesor por cada calificación
- Detección automática de estudiantes en riesgo académico

### Asistencia

- Registro diario con estados: presente, ausente, tarde, justificada
- Vista de heatmap de los últimos 90 días en el portal estudiantil
- Cálculo de porcentaje de asistencia por estudiante y grupo
- Reportes de asistencia exportables a Excel

### Reportes

- Boletines individuales en PDF
- Reportes de grupo en PDF
- Notas por grupo exportables a Excel
- Asistencia por grupo exportable a Excel
- Cuadro de honor con top estudiantes por grupo e institucional

### Portal del estudiante

- Login propio con su cédula como usuario
- Dashboard con KPIs personales (promedio, asistencia, próximas evaluaciones)
- Vista detallada de notas por materia con observaciones del profesor
- Vista de asistencia con heatmap visual de 90 días
- Aislamiento estricto: el estudiante solo ve sus propios datos
- Redirección automática al portal si intenta acceder a otras rutas

### Importación y mantenimiento

- Importador de estudiantes desde Excel con validación
- Papelera con restauración (soft delete de 30 días)
- Modo mantenimiento configurable desde panel de developer
- Feature flags para activar/desactivar funciones sin redeploy
- Backups manuales de la BD desde panel admin

### Interfaz de usuario

- Diseño responsive completo (mobile-first)
- Modo claro y oscuro con persistencia en localStorage
- Liquid glass aplicado en 30+ elementos del sistema
- Hover lift en cards y elementos navegables
- Sidebar colapsable con localStorage (atajo: Ctrl+B)
- Bottom navigation estilo iOS para móvil
- Sidebar con item activo estilo pill iOS
- Command palette de búsqueda global (atajo: Ctrl+K)
- Atajos de teclado para navegación rápida (g+d para dashboard, g+e para estudiantes, etc.)
- Tour interactivo de bienvenida para nuevos usuarios
- Toasts para notificaciones flash
- Modales personalizados (confirmación, credenciales generadas, atajos)
- Skeleton loading durante consultas lentas
- Tooltips contextuales
- Calendario integrado

### Optimización

- Caché de vistas de 45 segundos en dashboard (mejora medida: 347x)
- Lazy loading con joinedload en consultas con relaciones
- Asset versioning para cache busting automático del navegador
- Compresión gzip en producción
- Static files con cache busting por timestamp del deploy

### Email

- Notificaciones de credenciales nuevas
- Activación de cuentas por link
- Recuperación de contraseña
- Templates HTML responsive
- Configurable por variables de entorno

### Tests

- 46+ tests automatizados con pytest
- Cobertura de flujos críticos: login, 2FA, CRUD principal, permisos
- Fixtures con datos de prueba

---

## Estructura del proyecto

```
EduTrack/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models/                  # Modelos SQLAlchemy
│   │   ├── usuario.py
│   │   ├── estudiante.py
│   │   ├── profesor.py
│   │   ├── materia.py
│   │   ├── grupo.py
│   │   ├── evaluacion.py
│   │   ├── nota.py
│   │   ├── asistencia.py
│   │   ├── intento_login.py
│   │   └── configuracion.py
│   ├── routes/                  # Blueprints por dominio
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── students.py
│   │   ├── teachers.py
│   │   ├── subjects.py
│   │   ├── groups.py
│   │   ├── evaluations.py
│   │   ├── grades.py
│   │   ├── attendance.py
│   │   ├── reports.py
│   │   ├── honor.py
│   │   ├── portal.py
│   │   ├── main.py
│   │   └── dev.py
│   ├── services/                # Lógica de negocio
│   │   ├── reporte_service.py
│   │   ├── email_service.py
│   │   └── importer_service.py
│   ├── templates/               # Templates Jinja2
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── students/
│   │   ├── teachers/
│   │   ├── subjects/
│   │   ├── groups/
│   │   ├── evaluations/
│   │   ├── grades/
│   │   ├── attendance/
│   │   ├── reports/
│   │   ├── portal/
│   │   ├── errors/
│   │   └── emails/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── utils/                   # Helpers y utilidades
│       ├── forms.py
│       ├── decorators.py
│       ├── filters.py
│       └── timezone.py
├── migrations/                  # Migraciones Flask-Migrate
├── tests/                       # Tests pytest
├── config.py                    # Configuración por entorno
├── run.py                       # Entry point
├── setup_produccion.py          # Script de inicialización de BD
├── requirements.txt
├── Procfile                     # Para Render/Heroku
└── README.md
```

---

## Instalación local

### Requisitos previos

- Python 3.11 o superior
- pip
- Git
- (Opcional) PostgreSQL si quieres replicar el entorno de producción

### Pasos

1. Clonar el repositorio:

```bash
git clone https://github.com/andrickmarin592-debug/edutrack.git
cd edutrack
```

2. Crear y activar un entorno virtual:

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear archivo `.env` en la raíz del proyecto:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_aqui_minimo_32_caracteres
DATABASE_URL=sqlite:///edutrack.db

# Email (opcional para desarrollo, se imprime en consola si no se configura)
MAIL_ENABLED=false
```

5. Inicializar la base de datos:

```bash
python setup_produccion.py
```

Esto crea las tablas y los usuarios iniciales (ver sección de credenciales).

6. Ejecutar el servidor de desarrollo:

```bash
python run.py
```

Abrir `http://127.0.0.1:5000` en el navegador.

---

## Configuración del servidor de correos (Brevo)

EduTrack usa **Brevo** (ex-Sendinblue) como proveedor SMTP para envío de correos transaccionales (activación de cuenta, recuperación de contraseña, notificaciones).

### Cuenta gratuita de Brevo

El plan gratuito de Brevo permite **300 correos por día**, suficiente para un colegio.

### Pasos para configurar

1. Crear cuenta en [https://www.brevo.com](https://www.brevo.com)

2. Verificar el dominio del remitente:
   - Ir a **Settings → Senders, Domains & Dedicated IPs → Domains**
   - Agregar el dominio (ejemplo: `edu-track.school`)
   - Configurar los registros DNS solicitados (SPF, DKIM, DMARC) en Cloudflare
   - Esperar a que Brevo verifique el dominio (toma de 5 minutos a 24 horas)

3. Obtener las credenciales SMTP:
   - Ir a **Settings → SMTP & API → SMTP**
   - Generar una nueva **SMTP key**
   - Anotar el **login**, **server**, **port** y **password (smtpsib-...)**

4. Configurar las variables de entorno en producción (Render → Environment):

```env
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=tu_login@smtp-brevo.com
MAIL_PASSWORD=xsmtpsib-tu_key_completa_aqui
MAIL_DEFAULT_SENDER=noreply@edu-track.school
MAIL_ENABLED=true
PORTAL_URL=https://www.edu-track.school
```

5. Para desarrollo local, dejar `MAIL_ENABLED=false`. Los correos se imprimirán en consola en lugar de enviarse, lo cual es útil para depurar plantillas sin gastar el cupo de correos.

### Verificación

Después de configurar:

1. Crear un estudiante o profesor desde el sistema
2. Confirmar que llega el correo de activación al destinatario
3. Si no llega, revisar:
   - Carpeta de spam del destinatario
   - Logs de Render para mensajes de error de SMTP
   - Dashboard de Brevo en **Transactional → Statistics** para ver si el correo fue enviado y entregado

---

## Despliegue en producción

### Stack actual

- **Backend**: Render Web Service (plan Starter)
- **Base de datos**: Render PostgreSQL (plan Free o Starter)
- **DNS**: Cloudflare
- **Email**: Brevo SMTP (plan Free)

### Pasos para desplegar en Render

1. Conectar el repositorio de GitHub a Render como **Web Service**

2. Configurar el build:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`

3. Crear base de datos PostgreSQL en Render

4. Configurar variables de entorno (mínimo):

```env
SECRET_KEY=clave_aleatoria_segura_de_minimo_32_caracteres
DATABASE_URL=postgresql://... (Render lo genera automaticamente)
FLASK_ENV=production
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu_smtp_login
MAIL_PASSWORD=tu_smtp_password
MAIL_DEFAULT_SENDER=noreply@tu-dominio.com
MAIL_ENABLED=true
PORTAL_URL=https://tu-dominio.com
```

5. Inicializar la base de datos (solo la primera vez):
   - Render Dashboard → tu servicio → **Shell**
   - Ejecutar: `python setup_produccion.py`

6. Configurar el dominio personalizado:
   - Render → tu servicio → **Settings → Custom Domain**
   - Agregar el dominio
   - En Cloudflare, crear un registro CNAME apuntando al dominio de Render

---

## Credenciales por defecto

Después de ejecutar `setup_produccion.py`, el sistema crea estos usuarios:

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Super Admin | `developer` | `developer123` |
| Admin | `admin` | `admin123` |

**Cambiar estas contraseñas inmediatamente** después de la primera instalación.

Los profesores y estudiantes se crean desde el panel de administración. Por convención, el username de profesores y estudiantes es su **cédula**, y la contraseña inicial es generada automáticamente y mostrada en pantalla al crear la cuenta (también enviada por correo).

---

## Bugs conocidos

A continuación se listan los bugs identificados que están pendientes de resolver. Cada uno incluye una descripción, su impacto y un posible workaround.

### 1. Modo claro/oscuro requiere recargar al cambiar

**Descripción**: Al hacer click en el toggle de tema (sol/luna en la barra superior), algunos elementos visuales (como las KPI cards del dashboard) no actualizan sus colores correctamente al instante. El cambio queda en un estado visual inconsistente hasta que el usuario recarga la página manualmente.

**Causa identificada**: El JavaScript del toggle modifica el atributo `data-theme` del HTML, pero el CSS del sistema tiene reglas que mezclan dos selectores diferentes (`[data-theme="dark"]` y `.dark`), y la sincronización entre ambos no es instantánea en todos los elementos. Algunas reglas con variables CSS y gradientes complejos no se recalculan sin un repaint completo del navegador.

**Workaround actual**: Recargar la página después de cambiar el tema.

**Solución pendiente**: Auditar todas las reglas CSS del proyecto y unificar el uso de un solo selector (`[data-theme="dark"]`). Eliminar las reglas duplicadas con `.dark`. Forzar un repaint con técnicas como `display: none` momentáneo o usar `requestAnimationFrame` después del cambio.

**Severidad**: Baja. No afecta funcionalidad, solo experiencia visual.

---

### 2. Páginas se quedan en estado estático y requieren doble recarga

**Descripción**: En ocasiones, después de ciertas acciones (especialmente en Microsoft Edge), las páginas quedan en un estado donde los elementos interactivos no responden o muestran información desactualizada. Es necesario recargar la página dos veces (Ctrl+R o Ctrl+Shift+R) para que el contenido se actualice correctamente.

**Causa identificada**: Microsoft Edge tiene un sistema de caché agresivo llamado **back-forward cache (bfcache)** que mantiene páginas Flask renderizadas con contenido obsoleto. Aunque se implementó cache busting con `asset_version` para CSS y JS, y headers de `no-cache` para HTML, en algunos casos Edge mantiene la página en estado serializado.

**Workaround actual**:
1. Hacer Ctrl+Shift+R para forzar recarga completa
2. Para usuarios finales, recomendar Chrome o Firefox que tienen comportamiento más consistente
3. La página implementa un listener `pageshow` que detecta el restore desde bfcache, pero no funciona en todos los casos

**Solución pendiente**: Investigar el uso de la cabecera `Cache-Control: no-store` con `Vary: *` para forzar a Edge a nunca servir desde bfcache. También considerar agregar timestamps en las URLs de páginas críticas.

**Severidad**: Media. Afecta principalmente a usuarios de Edge en ciertos flujos.

---

### 3. Datos de múltiples instituciones se mezclarían

**Descripción**: El sistema actualmente no soporta multi-tenancy. Todos los datos viven en la misma base de datos sin separación por institución. Si en el futuro otro colegio comenzara a usar EduTrack en la misma instalación, los administradores de cualquier colegio verían los datos de todos los colegios.

**Causa identificada**: El diseño actual asume **una sola institución por instalación**. Las tablas (estudiantes, profesores, materias, grupos) no tienen una columna `institucion_id` que permita filtrar por organización.

**Workaround actual**: Solo desplegar la instancia para un colegio a la vez. Si se necesita servir a más colegios, crear instancias separadas con sus propias bases de datos.

**Solución pendiente**: Refactor mayor para implementar multi-tenancy (ver sección de pendientes).

**Severidad**: No aplica actualmente. Es una limitación de diseño que solo afecta si se quiere escalar a varios colegios.


---

### 5. Indentación inconsistente entre código pegado y archivos existentes

**Descripción**: Al pegar bloques de código desde un editor externo (o desde mensajes) al editor de GitHub, a veces se introducen tabs mezclados con espacios, lo cual rompe Python.

**Workaround actual**: Revisar visualmente la indentación antes de hacer commit. Asegurar que solo se usen espacios.

**Solución pendiente**: Configurar `.editorconfig` en el repositorio que defina espacios de 4 caracteres y end-of-line LF. Agregar pre-commit hooks con `black` o `autopep8`.

**Severidad**: Alta cuando ocurre. Mismo efecto que el bug 4.

---

## Pendientes y mejoras futuras

### Funcionalidades pendientes

#### Trabajo cotidiano con registro diario

Actualmente el tipo "trabajo cotidiano" existe como una evaluación más, pero el liceo lo califica día a día y luego promedia. Se necesita un módulo nuevo que permita al profesor agregar entradas diarias con puntaje y descripción, y que el sistema calcule el promedio automático que aporta a la nota final del trimestre.

#### Multi-tenancy (soporte para múltiples instituciones)

Refactor mayor para que el sistema soporte varios colegios en la misma instalación con aislamiento estricto de datos. Implica:

- Crear tabla `instituciones` con su configuración (nombre, logo, colores, etc.)
- Agregar columna `institucion_id` a todas las tablas principales
- Actualizar todas las consultas para filtrar por la institución del usuario activo
- Crear selector de institución en el login si el usuario pertenece a varias
- Sistema de onboarding para registrar nuevas instituciones
- Reportes consolidados para uso del MEP (si aplica)

#### API REST

Crear una API REST documentada con Swagger/OpenAPI para integración con sistemas externos del MEP o aplicaciones móviles nativas.

#### Aplicación móvil nativa

Construir una app en React Native o Flutter para que los estudiantes y padres accedan al portal desde el celular con notificaciones push.

#### Sistema de mensajería interna

Comunicación entre profesores, estudiantes y encargados dentro de la plataforma (foros por grupo, mensajes directos).

#### Calendario académico institucional

Vista de calendario con feriados, periodos de exámenes, entregas de proyectos, reuniones de padres.

#### Reportes para padres

Generar boletines en PDF firmados digitalmente para entregar a encargados, con código QR para verificar autenticidad.

#### Encuestas y formularios

Sistema para que la dirección envíe encuestas a profesores, estudiantes o encargados.

#### Sistema de cobros (si se monetiza)

Integración con SINPE Móvil o Stripe para que cada colegio pague su suscripción mensual.

---

### Mejoras técnicas pendientes

#### Backups automáticos

Configurar backups automáticos diarios de la BD PostgreSQL a un bucket de S3 o Backblaze B2. Actualmente solo se hacen backups manuales desde el panel admin.

#### Documentación técnica completa

Documentar:
- Diagrama de base de datos (ERD)
- Diagramas de secuencia de los flujos principales (login, 2FA, calificación, etc.)
- Guía de contribución para nuevos desarrolladores
- Manual de operaciones (cómo desplegar, cómo restaurar de un backup, cómo escalar)

#### Manual de usuario para profesores y administración

Documento PDF descargable con capturas paso a paso para cada flujo del sistema.

#### Tests de integración end-to-end

Agregar tests con Playwright o Selenium que prueben los flujos completos desde el navegador, no solo unitarios.

#### Performance del dashboard

El LCP (Largest Contentful Paint) actual del dashboard es de 5.12 segundos, lo cual es considerado lento por las métricas de Core Web Vitals. Mejoras pendientes:

- Agregar índices en PostgreSQL en las tablas `notas`, `asistencias`, `evaluaciones`, `estudiantes_grupo`
- Optimizar las consultas N+1 con `joinedload` y `selectinload`
- Implementar paginación virtual en listas largas
- Lazy loading de componentes pesados (gráficos)

#### Sistema de logging centralizado

Integrar con Sentry o Logtail para capturar errores en producción de forma centralizada y monitorear el sistema en tiempo real.

#### Healthcheck endpoint

Crear endpoint `/health` que reporte el estado de la BD, SMTP, y otros servicios externos. Útil para monitoreo con UptimeRobot o similar.

#### Rate limiting más fino

Actualmente el rate limiting es básico. Implementar Flask-Limiter con límites diferenciados por endpoint y rol de usuario.

#### Modo de mantenimiento programado

Mejorar el modo de mantenimiento para que muestre la fecha y hora estimada de regreso al servicio.

#### Internacionalización (i18n)

Agregar soporte para inglés además del español, para poder vender el sistema fuera de Costa Rica.

#### Tests automatizados de UI

Tests visuales con herramientas como Percy o Chromatic para detectar regresiones visuales después de cambios en CSS.

---

### Procesos pendientes

#### Constituir empresa o asociación

Si EduTrack pasa de proyecto educativo a producto comercial, formalizar la entidad legal con Hacienda y el registro nacional.

#### Política de privacidad y términos de uso

Documentos legales para que los colegios firmen al usar el sistema, especialmente importante por el manejo de datos de menores de edad.

#### Cumplimiento con Ley de Protección de Datos

Costa Rica tiene la Ley 8968 de Protección de la Persona Frente al Tratamiento de sus Datos Personales. EduTrack maneja datos sensibles de menores, lo cual requiere registro en la PRODHAB y cumplimiento estricto.

#### Acuerdo de servicio (SLA)

Definir compromisos de uptime, tiempo de respuesta a soporte, y procedimientos en caso de incidentes graves.

#### Plan de continuidad

Documentar qué pasa si los desarrolladores originales dejan el proyecto. Incluir traspaso de credenciales, documentación, accesos, etc.

---

## Autores

**Andrick Marín**


**Danier**
- Co-desarrollador

---

