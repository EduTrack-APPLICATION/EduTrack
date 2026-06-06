# 🎓 EduTrack — Sistema de Gestión Académica

**EduTrack** es una aplicación web profesional para la gestión académica de instituciones educativas. Permite administrar estudiantes, profesores, materias, grupos, evaluaciones, notas y asistencias, con generación automática de reportes en PDF y Excel.

Construido con **Python · Flask · PostgreSQL · Bootstrap 5**.

---

## ✨ Características principales

### Autenticación y roles
- Login con usuario **o** correo electrónico
- Dos roles: **administrador** y **profesor** (cada uno con su propio panel)
- Recuperación de contraseña vía token
- Cambio de contraseña personal desde el menú de usuario
- Protección CSRF en todos los formularios
- Sesiones seguras con Flask-Login

### Dashboard inteligente
- Tarjetas con métricas clave (estudiantes, grupos, evaluaciones, promedio general)
- Gráfico de **distribución de notas** (Chart.js)
- Gráfico de **asistencia de los últimos 14 días**
- Listado de **estudiantes en riesgo académico**
- Actividad reciente y próximas evaluaciones

### CRUDs completos
- **Estudiantes**: con código, cédula, datos de contacto, encargado, estado académico (activo/inactivo/graduado/retirado), búsqueda y filtros
- **Profesores**: con cuenta de usuario asociada, especialidad, título académico, asignación de materias
- **Materias**: con créditos, horas semanales, activación/desactivación
- **Grupos**: vinculan materia + profesor titular + estudiantes; matriculación/desmatriculación desde un modal
- **Evaluaciones**: 7 tipos (examen, quiz, tarea, proyecto, exposición, práctica, participación), con puntaje máximo y peso porcentual

### Sistema de notas (dos modos)
- **Modo grupal**: tabla con toda la lista del grupo, una fila por estudiante, auto-guardado en cada cambio (AJAX)
- **Modo individual**: edición uno a uno desde el detalle del estudiante
- Navegación por teclado: <kbd>↓</kbd> / <kbd>Enter</kbd> avanza al siguiente, <kbd>↑</kbd> retrocede
- Validación automática de rango (0 ≤ puntaje ≤ puntaje_máximo)
- Indicador visual de estado por fila (guardando / guardado / error)
- Cálculo automático de:
  - **Nota final** ponderada por porcentaje de cada evaluación
  - **Estado académico**: aprobado (≥70), recuperación (60-69), reprobado (<60)
  - **Porcentaje del curso cubierto** por las evaluaciones ya hechas

### Control de asistencia
- Toma de asistencia día a día, grupo a grupo
- Cuatro estados: **P**resente, **A**usente, **J**ustificado, **T**ardía
- Botones de marcar masivo ("todos presentes", "todos ausentes")
- Vista de historial en formato **matriz** (estudiantes × fechas)
- Cálculo automático del porcentaje de asistencia por estudiante

### Reportes (PDF y Excel)
- **Boletín individual del estudiante** (PDF con notas, asistencia, observaciones)
- **Reporte de grupo** (PDF con todos los estudiantes y su desempeño)
- **Notas detalladas de grupo** (Excel con todas las evaluaciones y notas por estudiante)
- **Asistencia de grupo** (Excel con matriz de asistencia y porcentajes)
- Reportes generados con ReportLab + OpenPyXL, paleta de colores corporativa

### Alertas automáticas
- Estudiantes con nota promedio < 70
- Estudiantes con asistencia < 80%
- Alertas individuales mostradas en el detalle del estudiante

### Interfaz moderna
- Sidebar fijo de navegación con secciones temáticas
- Header con buscador, alternador de tema y menú de usuario
- **Modo claro y oscuro** (persistido en `localStorage`)
- Responsive (sidebar colapsable en móvil)
- Tipografía **Inter**, iconografía **Bootstrap Icons**
- Gradientes y sombras sutiles, animaciones suaves

---

## 🛠️ Stack técnico

| Capa | Tecnología |
|------|------------|
| **Backend** | Python 3.11+, Flask 3.0, Flask-SQLAlchemy 3.1, Flask-Login, Flask-WTF, Flask-Bcrypt, Flask-Migrate |
| **Base de datos** | PostgreSQL (producción) / SQLite (desarrollo) |
| **Frontend** | HTML5, CSS3, JavaScript (vanilla), Bootstrap 5.3, Bootstrap Icons, Chart.js |
| **Reportes** | ReportLab (PDF), OpenPyXL (Excel), Pandas |
| **Despliegue** | Gunicorn + Procfile (compatible con Heroku, Render, Railway) |

---

## 📦 Instalación rápida (3 comandos)

EduTrack viene configurado para funcionar con **SQLite** sin necesidad de instalar nada extra.

### Requisitos
- **Python 3.10 o superior** ([descargar aquí](https://www.python.org/downloads/))

### Instalación

```powershell
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Setup automático (crea .env, BD y datos de prueba)
python setup.py

# 3. Arrancar
python run.py
```

Abre tu navegador en **http://127.0.0.1:5000** e inicia sesión:

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Administrador | `admin` | `admin123` |
| Profesor | `mrodriguez` | `profesor123` |

---

### 📦 Instalación detallada (opcional)

Si prefieres entender cada paso:

```powershell
# 1. Entorno virtual (opcional pero recomendado)
python -m venv .venv
.venv\Scripts\activate          # En Linux/Mac: source .venv/bin/activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Configuración
copy .env.example .env          # En Linux/Mac: cp .env.example .env

# 4. Crear tablas + datos de prueba
python setup.py

# 5. Arrancar
python run.py
```

### Cambiar a PostgreSQL (producción)

Edita `.env`:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/edutrack
```

E instala el driver:

```bash
pip install psycopg2-binary
```
- Evaluaciones, notas y registros de asistencia ficticios

### 6. Arrancar el servidor

```bash
flask --app run.py run --debug
# o simplemente:
python run.py
```

Visita 👉 **http://127.0.0.1:5000**

---

## 🔑 Credenciales de prueba

| Rol           | Usuario       | Contraseña    |
|---------------|---------------|---------------|
| Administrador | `admin`       | `admin123`    |
| Profesor      | `mrodriguez`  | `profesor123` |
| Profesor      | `jgomez`      | `profesor123` |
| Profesor      | `avargas`     | `profesor123` |
| Profesor      | `cmendez`     | `profesor123` |
| Profesor      | `lcastro`     | `profesor123` |

⚠️ **Cambia estas contraseñas antes de poner en producción.**

---

## 🚀 Despliegue en producción

### Con Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

### En Heroku / Render / Railway

El `Procfile` ya está configurado:

```
web: gunicorn "app:create_app('production')"
```

Variables de entorno requeridas en el panel:

- `SECRET_KEY` — clave generada con `secrets.token_hex(32)`
- `DATABASE_URL` — URL de PostgreSQL (la mayoría de plataformas la proveen)
- `FLASK_CONFIG=production`

### Migraciones de base de datos

Si modificas los modelos, usa Flask-Migrate:

```bash
flask --app run.py db migrate -m "descripción del cambio"
flask --app run.py db upgrade
```

---

## 🔐 HTTPS y seguridad en producción

EduTrack incluye **Flask-Talisman**, que activa automáticamente HTTPS y cabeceras de seguridad cuando la app corre con `FLASK_CONFIG=production`. **En desarrollo todo sigue funcionando con HTTP**, sin cambios.

### Qué se activa automáticamente en producción

| Cabecera | Valor | Para qué sirve |
|----------|-------|----------------|
| **Strict-Transport-Security** | `max-age=31536000; includeSubDomains` | Obliga al navegador a usar HTTPS por 1 año |
| **Content-Security-Policy** | `default-src 'self'` + CDNs permitidos | Bloquea scripts maliciosos / XSS |
| **X-Frame-Options** | `DENY` | Bloquea clickjacking (que tu sitio sea cargado en un `<iframe>`) |
| **X-Content-Type-Options** | `nosniff` | Bloquea ataques de MIME confusion |
| **Referrer-Policy** | `strict-origin-when-cross-origin` | Controla qué información del referrer se envía |

Además, las cookies de sesión se marcan como `Secure` y `HttpOnly`.

### Variable de entorno relevante

En el `.env` de producción:

```env
FLASK_CONFIG=production
FORCE_HTTPS=true       # opcional, por defecto true
```

Si tu plataforma de hosting (Heroku, Render, Cloudflare, etc.) ya termina HTTPS en el balanceador y la app recibe HTTP internamente, puedes desactivar el redirect con:

```env
FORCE_HTTPS=false
```

### Conseguir un certificado SSL real

**Opción A — Plataforma cloud (más fácil):**
Heroku, Render, Railway, Fly.io y Vercel proveen HTTPS automáticamente al asignar un dominio. **No necesitas configurar nada más.**

**Opción B — Servidor propio (VPS) con Let's Encrypt:**

```bash
# 1. Instala Nginx como proxy reverso
sudo apt install nginx certbot python3-certbot-nginx

# 2. Configura un virtual host en Nginx que apunte a tu app (puerto 8000)
sudo nano /etc/nginx/sites-available/edutrack
```

Contenido del virtual host:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 3. Activa el sitio y obtén el certificado
sudo ln -s /etc/nginx/sites-available/edutrack /etc/nginx/sites-enabled/
sudo certbot --nginx -d tu-dominio.com
sudo systemctl reload nginx
```

Let's Encrypt te renovará el certificado automáticamente cada 90 días.

### Probar HTTPS en local (autofirmado)

Para verificar que las cabeceras funcionan **sin desplegar**, puedes correr la app con un certificado autofirmado:

```bash
pip install pyOpenSSL
flask --app run.py run-https
```

Visita https://localhost:5000 — el navegador mostrará una advertencia (porque el cert es autofirmado), aceptas y verás la app con HTTPS real. Útil para confirmar que el CSP y demás no bloquean nada antes de subir a producción.

---

## 🏆 Cuadro de Honor

EduTrack genera automáticamente un **ranking de los mejores estudiantes** por promedio académico, con diplomas en PDF imprimibles.

### Características

- **Top N configurable** (3, 5, 10, 20, 50)
- Filtros por **grupo**, **materia**, **periodo** o **año**
- **Podio visual** para los primeros 3 lugares (oro, plata, bronce)
- **Diploma individual** en PDF para cualquier estudiante
- **Diplomas en lote** — un único PDF con todos los diplomas del top, listo para imprimir
- Manejo correcto de **empates** (regla olímpica: dos estudiantes con el mismo promedio comparten posición)
- **Permisos automáticos**: los profesores solo ven los estudiantes de sus propios grupos

### Acceso

Desde el sidebar → **Reportes** → **Cuadro de Honor**, o directamente en `/cuadro-honor/`.

### Cálculo del promedio

El promedio que aparece en el ranking se calcula así:

```
promedio_estudiante = Σ(nota_final_grupo) / total_grupos_evaluados
```

Donde `nota_final_grupo` es la nota ponderada del estudiante en cada uno de sus grupos (la misma fórmula que se usa para el estado académico).

Los estudiantes **sin notas registradas son excluidos automáticamente** del ranking.

---

## 📁 Estructura del proyecto

```
edutrack/
├── app/
│   ├── __init__.py           # Application Factory (create_app)
│   ├── models/               # Modelos SQLAlchemy
│   │   ├── usuario.py        # Usuario + autenticación
│   │   ├── profesor.py       # Profesor + asignación de materias
│   │   ├── estudiante.py
│   │   ├── materia.py
│   │   ├── grupo.py          # Grupo + matriculación
│   │   ├── evaluacion.py     # Evaluaciones + tipos
│   │   ├── nota.py
│   │   └── asistencia.py
│   ├── routes/               # Blueprints (controladores)
│   │   ├── auth.py           # Login, logout, recuperación
│   │   ├── dashboard.py      # Dashboard + APIs de gráficos
│   │   ├── students.py
│   │   ├── teachers.py
│   │   ├── subjects.py
│   │   ├── groups.py
│   │   ├── evaluations.py
│   │   ├── grades.py         # Calificación grupal + AJAX
│   │   ├── attendance.py
│   │   ├── reports.py
│   │   └── main.py
│   ├── services/             # Lógica de negocio
│   │   ├── calculo_service.py    # Notas finales, estados, alertas
│   │   └── reporte_service.py    # PDF (ReportLab) y Excel (OpenPyXL)
│   ├── utils/
│   │   ├── decorators.py     # @admin_required, @profesor_or_admin
│   │   ├── filters.py        # Filtros Jinja personalizados
│   │   ├── forms.py          # WTForms
│   │   └── seed_data.py      # Datos de prueba
│   ├── templates/            # Plantillas Jinja2
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── students/, teachers/, subjects/, groups/
│   │   ├── evaluations/, grades/, attendance/
│   │   ├── reports/
│   │   └── errors/
│   └── static/
│       ├── css/style.css     # Design system completo
│       └── js/app.js         # Tema, sidebar, AJAX, atajos teclado
├── config.py                 # Configuración (dev/test/prod)
├── run.py                    # Entry point + CLI commands
├── requirements.txt
├── Procfile                  # Despliegue Heroku/Render
├── .env.example
└── README.md
```

---

## 🧮 Lógica de cálculo de notas

### Nota final (ponderada)

Si un estudiante tiene varias evaluaciones, la **nota final** se calcula como:

```
nota_final = Σ ( (puntaje / puntaje_máximo) × 100 × (porcentaje_evaluación / 100) )
```

Por ejemplo, con dos evaluaciones:
- Examen (peso 60%): 80/100 → contribuye 48 puntos
- Quiz (peso 40%): 70/100 → contribuye 28 puntos
- **Nota final: 76**

### Estado académico

| Nota final | Estado          | Color    |
|------------|-----------------|----------|
| ≥ 70       | Aprobado        | success  |
| 60 – 69    | Recuperación    | warning  |
| < 60       | Reprobado       | danger   |

Si aún no se ha cubierto el 100% del peso evaluativo, los estados se marcan como *"en curso"*.

Los umbrales se configuran en `config.py`:

```python
NOTA_MINIMA_APROBACION = 70
NOTA_RECUPERACION      = 60
ASISTENCIA_MINIMA      = 80
```

---

## 🎨 Personalización

### Cambiar paleta de colores

Edita `app/static/css/style.css`:

```css
:root {
    --primary:   #3b82f6;   /* azul */
    --secondary: #6366f1;   /* índigo */
    --success:   #10b981;   /* verde */
    --warning:   #f59e0b;   /* amarillo */
    --danger:    #ef4444;   /* rojo */
}
```

### Cambiar el nombre/marca

Reemplaza "EduTrack" en `app/templates/base.html` y `app/templates/auth/login.html`.

---

## 🐛 Solución de problemas

**`No module named 'psycopg2'`**
Si usas PostgreSQL, instala:
```bash
pip install psycopg2-binary
```

**`Address already in use`**
Otro proceso usa el puerto 5000:
```bash
flask --app run.py run --port 5001
```

**Las tablas no se crean**
Verifica que `DATABASE_URL` apunte a una base de datos existente, luego:
```bash
flask --app run.py init-db
```

---

## 📄 Licencia

Este proyecto fue creado como sistema base de gestión académica. Úsalo, modifícalo y distribúyelo libremente.

---

**EduTrack** · Sistema de Gestión Académica · Hecho con ❤️ usando Flask
