"""
Modelo Profesor y su asignación a materias.
"""
from datetime import datetime
from app import db


class ProfesorMateria(db.Model):
    """Tabla pivote: profesores asignados a materias."""
    __tablename__ = 'profesor_materia'

    id = db.Column(db.Integer, primary_key=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id', ondelete='CASCADE'), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materias.id', ondelete='CASCADE'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('profesor_id', 'materia_id', name='uq_profesor_materia'),
    )


class Profesor(db.Model):
    __tablename__ = 'profesores'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'),
                           unique=True, nullable=False)
    cedula = db.Column(db.String(30), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    telefono = db.Column(db.String(30))
    direccion = db.Column(db.String(255))
    especialidad = db.Column(db.String(100))
    titulo = db.Column(db.String(150))
    fecha_ingreso = db.Column(db.Date, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    materias = db.relationship('Materia', secondary='profesor_materia',
                                backref=db.backref('profesores', lazy='dynamic'),
                                lazy='dynamic')
    grupos = db.relationship('Grupo', backref='profesor_titular', lazy='dynamic')
    evaluaciones = db.relationship('Evaluacion', backref='profesor', lazy='dynamic')

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'

    @property
    def email(self):
        """Email del profesor (delegado al Usuario asociado)."""
        return self.usuario.email if self.usuario else None

    @property
    def username(self):
        """Username del profesor (delegado al Usuario asociado)."""
        return self.usuario.username if self.usuario else None

    def __repr__(self):
        return f'<Profesor {self.nombre_completo}>'
