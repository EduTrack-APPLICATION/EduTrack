## 🚀 Arquitectura y Decisiones del Proyecto

Este proyecto utiliza una infraestructura en la nube moderna y altamente escalable. Inicialmente se contemplaron diferentes proveedores de bases de datos, pero se seleccionó **Supabase (Plan Pro)** como la solución central debido a su rendimiento, herramientas integradas y capacidad de almacenamiento.

A continuación se detallan las razones técnicas y los límites del plan que respaldan la estabilidad de esta aplicación escolar.

---

### 📊 Infraestructura: Supabase Pro ($25/mes)

Para garantizar la disponibilidad constante para profesores y alumnos, el proyecto opera bajo el entorno de producción de Supabase Pro, el cual ofrece los siguientes recursos:

*   **🗄️ Base de Datos (PostgreSQL):** **8 GB incluidos** de almacenamiento dedicados exclusivamente a texto (registros de usuarios, tablas de materias, calificaciones y metadatos de tareas).
*   **📂 Almacenamiento de Archivos (Storage):** **100 GB incluidos** para almacenar de forma nativa todos los PDFs, imágenes, exámenes y guías de estudio que suban los profesores.
*   **🌐 Transferencia de Red (Egress):** **250 GB mensuales gratuitos** de ancho de banda saliente, asegurando que miles de estudiantes puedan descargar sus recursos didácticos simultáneamente sin costes adicionales.
*   **⏱️ Disponibilidad Permanente:** Se elimina la pausa por inactividad del plan gratuito. La base de datos se mantiene encendida 24/7, garantizando acceso incluso durante los periodos vacacionales.

---

### 🛡️ Beneficios Clave para el Entorno Escolar

1. **Autenticación Integrada:** Gestión nativa de sesiones para un máximo de **100,000 usuarios activos mensuales**, ideal para segmentar accesos de Directivos, Profesores y Alumnos.
2. **Seguridad a Nivel de Filas (RLS):** Permite restringir el acceso a los archivos de forma estricta. Un alumno solo puede ver las tareas de su respectivo salón o profesor, protegiendo exámenes e información confidencial.
3. **Copias de Seguridad:** Respaldos automáticos diarios con retención de **7 días** para prevenir cualquier pérdida accidental de notas o registros académicos.
4. **Precio Fijo y Predecible:** Evita sorpresas en la facturación mediante una tarifa plana mensual que cubre todo el backend en un solo lugar.









## 🌐 Despliegue del Frontend y Backend Lógico: Vercel (Plan Hobby)

Para el alojamiento de la lógica de la aplicación en **Flask (Python)** y la interfaz de usuario, se seleccionó **Vercel** como proveedor de infraestructura de cómputo. Su arquitectura basada en funciones *Serverless* optimiza los recursos para el tráfico de la comunidad estudiantil.

A continuación se detallan las especificaciones técnicas y beneficios de este entorno de despliegue:

*   **⏱️ Carga Instantánea (Sin Cold Starts):** A diferencia de servidores tradicionales, Vercel ejecuta las rutas de Flask bajo demanda en milisegundos. La aplicación nunca entra en estado "dormido", garantizando disponibilidad inmediata para los alumnos a cualquier hora.
*   **🌐 Red de Distribución Global (CDN):** El HTML, CSS y JavaScript generados por Python se distribuyen de forma ultra rápida a través de la red global de Vercel, minimizando la latencia y el tiempo de respuesta en los dispositivos de los usuarios.
*   **⚡ Horas de Cómputo Ilimitadas:** Al fragmentar el código en funciones nativas independientes, se elimina el límite de horas mensuales continuas, permitiendo que la plataforma esté activa 24/7 sin riesgo de caídas a fin de mes.
*   **📊 Ancho de Banda Eficiente:** Dispone de **100 GB mensuales gratuitos** dedicados exclusivamente a la transferencia del código y las plantillas del sistema. Al estar los archivos pesados (PDFs e imágenes) alojados en Supabase Pro, este margen es más que suficiente para dar soporte a un flujo constante de 500 estudiantes.

---

### 🛠️ Flujo de Integración Continua (CI/CD)

*   **Automatización con GitHub:** Cada cambio o actualización que se sube a la rama principal de este repositorio (`git push`) genera un despliegue automático inmediato en producción a través de Vercel.
*   **Arquitectura Desacoplada:** Vercel se encarga exclusivamente de procesar las peticiones HTTP y renderizar las vistas, utilizando variables de entorno protegidas (`DATABASE_URL`) para comunicarse de forma segura con la base de datos Postgres de Supabase.
