"""
Modelo Materia.
"""
from datetime import datetime
from app import db


class Materia(db.Model):
    __tablename__ = 'materias'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    creditos = db.Column(db.Integer, default=3)
    horas_semana = db.Column(db.Integer, default=4)
    activa = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    grupos = db.relationship('Grupo', backref='materia', lazy='dynamic')
    evaluaciones = db.relationship('Evaluacion', backref='materia', lazy='dynamic')

    def __repr__(self):
        return f'<Materia {self.codigo} - {self.nombre}>'
