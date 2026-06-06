"""
Carga de datos de prueba para EduTrack.
Ejecutar con: flask seed-db
"""
import random
from datetime import date, timedelta
from app import db
from app.models import (
    Usuario, Profesor, Estudiante, Materia, Grupo, Evaluacion, Nota, Asistencia,
    RolEnum, EstadoEstudianteEnum, TipoEvaluacionEnum, EstadoAsistenciaEnum
)


def seed_database():
    """Carga datos de prueba completos."""
    print('🌱 Iniciando carga de datos de prueba...')

    # Limpiar todo y recrear
    db.drop_all()
    db.create_all()

    # ====== USUARIOS Y PROFESORES ======
    # Super admin (developer) — solo se crea si no existe ningún super_admin
    if not Usuario.query.filter_by(rol=RolEnum.SUPER_ADMIN.value).first():
        super_admin = Usuario(
            username='developer',
            email='dev@edutrack.com',
            nombre_completo='Developer',
            rol=RolEnum.SUPER_ADMIN.value
        )
        super_admin.set_password('developer123')
        super_admin.forzar_cambio_password = True
        db.session.add(super_admin)

    admin = Usuario(
        username='admin',
        email='admin@edutrack.com',
        nombre_completo='Administrador General',
        rol=RolEnum.ADMIN.value
    )
    admin.set_password('admin123')
    admin.forzar_cambio_password = True
    db.session.add(admin)

    profesores_data = [
        ('mrodriguez', 'maria.rodriguez@edutrack.com', 'María', 'Rodríguez',
         '1-1111-1111', 'Matemáticas', 'Licenciada en Matemáticas'),
        ('jgomez', 'juan.gomez@edutrack.com', 'Juan', 'Gómez',
         '1-2222-2222', 'Ciencias Naturales', 'Máster en Biología'),
        ('avargas', 'ana.vargas@edutrack.com', 'Ana', 'Vargas',
         '1-3333-3333', 'Español', 'Licenciada en Letras'),
        ('cmendez', 'carlos.mendez@edutrack.com', 'Carlos', 'Méndez',
         '1-4444-4444', 'Computación', 'Ing. Sistemas'),
        ('lcastro', 'laura.castro@edutrack.com', 'Laura', 'Castro',
         '1-5555-5555', 'Estudios Sociales', 'Licenciada en Historia'),
    ]

    profesores = []
    for username, email, nombre, apellido, ced, esp, titulo in profesores_data:
        u = Usuario(
            username=username, email=email,
            nombre_completo=f'{nombre} {apellido}',
            rol=RolEnum.PROFESOR.value
        )
        u.set_password('profesor123')
        u.forzar_cambio_password = True
        db.session.add(u)
        db.session.flush()

        p = Profesor(
            usuario_id=u.id, cedula=ced, nombre=nombre, apellido=apellido,
            telefono='+506 ' + ced.replace('-', ''), especialidad=esp, titulo=titulo
        )
        db.session.add(p)
        profesores.append(p)
    db.session.flush()

    # ====== MATERIAS ======
    materias_data = [
        ('MAT-101', 'Matemática I', 'Álgebra y aritmética básica', 4, 5),
        ('MAT-201', 'Matemática II', 'Geometría y trigonometría', 4, 5),
        ('CIE-101', 'Ciencias Naturales', 'Biología, química y física básica', 3, 4),
        ('ESP-101', 'Español', 'Comprensión lectora y redacción', 3, 4),
        ('SOC-101', 'Estudios Sociales', 'Historia y geografía', 3, 4),
        ('COM-101', 'Informática', 'Computación y ofimática', 2, 3),
    ]

    materias = []
    for cod, nom, desc, cred, horas in materias_data:
        m = Materia(codigo=cod, nombre=nom, descripcion=desc, creditos=cred, horas_semana=horas)
        db.session.add(m)
        materias.append(m)
    db.session.flush()

    # Asignar materias a profesores (según especialidad)
    profesores[0].materias.append(materias[0])  # María - Mat I
    profesores[0].materias.append(materias[1])  # María - Mat II
    profesores[1].materias.append(materias[2])  # Juan - Ciencias
    profesores[2].materias.append(materias[3])  # Ana - Español
    profesores[3].materias.append(materias[5])  # Carlos - Informática
    profesores[4].materias.append(materias[4])  # Laura - Sociales

    # ====== ESTUDIANTES ======
    nombres = ['Ana', 'Pedro', 'María', 'Luis', 'Sofía', 'Carlos', 'Lucía', 'Diego',
                'Camila', 'Andrés', 'Valentina', 'Mateo', 'Isabella', 'Sebastián',
                'Emma', 'Tomás', 'Mariana', 'Joaquín', 'Antonella', 'Benjamín',
                'Catalina', 'Daniel', 'Elena', 'Felipe', 'Gabriela']
    apellidos = ['García', 'Martínez', 'López', 'Sánchez', 'Pérez', 'Ramírez',
                  'Torres', 'Flores', 'Rivera', 'Cruz', 'Morales', 'Castillo',
                  'Vargas', 'Romero', 'Hernández', 'Jiménez', 'Mendoza', 'Ruiz']

    estudiantes = []
    for i in range(30):
        nom = random.choice(nombres)
        ape = random.choice(apellidos)
        e = Estudiante(
            codigo=f'EST-{2026000 + i + 1}',
            cedula=f'1-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
            nombre=nom,
            apellido=ape,
            email=f'{nom.lower()}.{ape.lower()}{i}@estudiante.edutrack.com',
            telefono=f'+506 8{random.randint(1000000, 9999999)}',
            fecha_nacimiento=date(2008 + random.randint(0, 3),
                                   random.randint(1, 12),
                                   random.randint(1, 28)),
            direccion=f'San José, Costa Rica',
            seccion=random.choice(['10-A', '10-B', '11-A', '11-B']),
            encargado=f'{random.choice(nombres)} {ape}',
            telefono_encargado=f'+506 7{random.randint(1000000, 9999999)}',
            estado=EstadoEstudianteEnum.ACTIVO.value,
        )
        db.session.add(e)
        estudiantes.append(e)
    db.session.flush()

    # ====== GRUPOS ======
    grupos_data = [
        ('MAT101-A-26', 'Matemática I - Grupo A', materias[0], profesores[0], 'Aula 101', 'L-M-V 8:00-9:30'),
        ('MAT101-B-26', 'Matemática I - Grupo B', materias[0], profesores[0], 'Aula 102', 'M-J 10:00-11:30'),
        ('CIE101-A-26', 'Ciencias Naturales - A', materias[2], profesores[1], 'Lab 201', 'M-J 8:00-9:30'),
        ('ESP101-A-26', 'Español - Grupo A', materias[3], profesores[2], 'Aula 103', 'L-M-V 9:30-11:00'),
        ('COM101-A-26', 'Informática - Grupo A', materias[5], profesores[3], 'Lab Comp', 'V 13:00-15:00'),
        ('SOC101-A-26', 'Estudios Sociales - A', materias[4], profesores[4], 'Aula 104', 'M-J 13:00-14:30'),
    ]

    grupos = []
    for cod, nom, mat, prof, aula, hor in grupos_data:
        g = Grupo(
            codigo=cod, nombre=nom, materia_id=mat.id, profesor_id=prof.id,
            periodo='2026-I', anio=2026, cupo_maximo=35, aula=aula, horario=hor
        )
        db.session.add(g)
        grupos.append(g)
    db.session.flush()

    # Matricular estudiantes en grupos (cada estudiante en 3 grupos)
    for est in estudiantes:
        grupos_aleatorios = random.sample(grupos, 3)
        for g in grupos_aleatorios:
            g.estudiantes.append(est)

    db.session.flush()

    # ====== EVALUACIONES Y NOTAS ======
    plantilla_evaluaciones = [
        ('Quiz 1', TipoEvaluacionEnum.QUIZ.value, 10, 100, -45),
        ('Tarea 1', TipoEvaluacionEnum.TAREA.value, 15, 100, -30),
        ('Examen Parcial', TipoEvaluacionEnum.EXAMEN.value, 25, 100, -15),
        ('Proyecto', TipoEvaluacionEnum.PROYECTO.value, 20, 100, -5),
    ]

    for grupo in grupos:
        for nombre, tipo, porcentaje, max_pts, dias_offset in plantilla_evaluaciones:
            ev = Evaluacion(
                nombre=nombre,
                descripcion=f'{nombre} de {grupo.materia.nombre}',
                tipo=tipo,
                fecha=date.today() + timedelta(days=dias_offset),
                puntaje_maximo=max_pts,
                porcentaje=porcentaje,
                materia_id=grupo.materia_id,
                grupo_id=grupo.id,
                profesor_id=grupo.profesor_id,
            )
            db.session.add(ev)
            db.session.flush()

            # Generar notas (no para todas las evaluaciones, simulando reales)
            if dias_offset < -10:  # solo evaluaciones ya pasadas
                for est in grupo.estudiantes:
                    # Distribución realista: 70% buena, 20% regular, 10% baja
                    r = random.random()
                    if r < 0.7:
                        puntaje = random.uniform(70, 100)
                    elif r < 0.9:
                        puntaje = random.uniform(55, 70)
                    else:
                        puntaje = random.uniform(30, 55)
                    nota = Nota(
                        estudiante_id=est.id,
                        evaluacion_id=ev.id,
                        puntaje=round(puntaje, 1),
                    )
                    db.session.add(nota)

    # ====== ASISTENCIA ======
    # Generar 10 días de asistencia para cada grupo
    for grupo in grupos:
        for dias_atras in range(10):
            fecha_asist = date.today() - timedelta(days=dias_atras * 2)
            for est in grupo.estudiantes:
                r = random.random()
                if r < 0.85:
                    estado = EstadoAsistenciaEnum.PRESENTE.value
                elif r < 0.92:
                    estado = EstadoAsistenciaEnum.TARDIA.value
                elif r < 0.97:
                    estado = EstadoAsistenciaEnum.JUSTIFICADO.value
                else:
                    estado = EstadoAsistenciaEnum.AUSENTE.value
                a = Asistencia(
                    estudiante_id=est.id,
                    grupo_id=grupo.id,
                    fecha=fecha_asist,
                    estado=estado,
                )
                db.session.add(a)

    db.session.commit()
    print('✓ Datos de prueba cargados:')
    print(f'  - 1 administrador (usuario: admin, contraseña: admin123)')
    print(f'  - {len(profesores)} profesores (contraseña: profesor123)')
    print(f'  - {len(materias)} materias')
    print(f'  - {len(grupos)} grupos')
    print(f'  - {len(estudiantes)} estudiantes')
    print(f'  - Evaluaciones, notas y asistencias generadas.')
