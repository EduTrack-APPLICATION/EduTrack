"""
Modelo Estudiante.
"""
from datetime import datetime
from enum import Enum
from app import db


class EstadoEstudianteEnum(str, Enum):
    ACTIVO = 'activo'
    INACTIVO = 'inactivo'
    GRADUADO = 'graduado'
    RETIRADO = 'retirado'


class Estudiante(db.Model):
    __tablename__ = 'estudiantes'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True, nullable=False, index=True)
    cedula = db.Column(db.String(30), unique=True, nullable=True, index=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True)
    telefono = db.Column(db.String(30))
    fecha_nacimiento = db.Column(db.Date)
    direccion = db.Column(db.String(255))
    seccion = db.Column(db.String(50))
    encargado = db.Column(db.String(150))
    telefono_encargado = db.Column(db.String(30))
    estado = db.Column(db.String(20), default=EstadoEstudianteEnum.ACTIVO.value, nullable=False)
    fecha_ingreso = db.Column(db.Date, default=datetime.utcnow)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    eliminado_en = db.Column(db.DateTime, nullable=True, index=True)

    # Relaciones
    notas = db.relationship('Nota', backref='estudiante', lazy='dynamic',
                            cascade='all, delete-orphan')
    asistencias = db.relationship('Asistencia', backref='estudiante', lazy='dynamic',
                                   cascade='all, delete-orphan')
    grupos = db.relationship('Grupo', secondary='estudiante_grupo',
                              backref=db.backref('estudiantes', lazy='dynamic'),
                              lazy='dynamic')

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        today = datetime.today().date()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    def __repr__(self):
        return f'<Estudiante {self.codigo} - {self.nombre_completo}>'
