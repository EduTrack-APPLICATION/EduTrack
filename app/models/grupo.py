"""
Modelo Grupo: agrupa estudiantes en una materia con un profesor titular.
"""
from datetime import datetime
from app import db


class EstudianteGrupo(db.Model):
    """Tabla pivote: estudiantes matriculados en grupos."""
    __tablename__ = 'estudiante_grupo'

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id', ondelete='CASCADE'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id', ondelete='CASCADE'), nullable=False)
    fecha_matricula = db.Column(db.DateTime, default=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint('estudiante_id', 'grupo_id', name='uq_estudiante_grupo'),
    )


class Grupo(db.Model):
    __tablename__ = 'grupos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(120), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materias.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id'), nullable=False)
    periodo = db.Column(db.String(20), nullable=False)  # ej: '2026-I', '2026-II'
    anio = db.Column(db.Integer, nullable=False, default=datetime.utcnow().year)
    cupo_maximo = db.Column(db.Integer, default=40)
    aula = db.Column(db.String(50))
    horario = db.Column(db.String(120))
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    evaluaciones = db.relationship('Evaluacion', backref='grupo', lazy='dynamic',
                                    cascade='all, delete-orphan')
    asistencias = db.relationship('Asistencia', backref='grupo', lazy='dynamic',
                                   cascade='all, delete-orphan')

    @property
    def total_estudiantes(self):
        return self.estudiantes.count()

    @property
    def cupos_disponibles(self):
        return self.cupo_maximo - self.total_estudiantes

    @property
    def profesor(self):
        """Alias del profesor titular (para conveniencia en plantillas)."""
        return self.profesor_titular

    def __repr__(self):
        return f'<Grupo {self.codigo} - {self.nombre}>'
