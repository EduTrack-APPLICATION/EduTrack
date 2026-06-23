"""
Modelo Evaluacion: exámenes, quices, tareas, proyectos, etc.
"""
from datetime import datetime, date
from enum import Enum
from app import db


class TipoEvaluacionEnum(str, Enum):
    EXAMEN = 'examen'
    QUIZ = 'quiz'
    TAREA = 'tarea'
    PROYECTO = 'proyecto'
    EXPOSICION = 'exposicion'
    PRACTICA = 'practica'
    PARTICIPACION = 'participacion'
    COTIDIANO = 'cotidiano'


class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(30), nullable=False, default=TipoEvaluacionEnum.TAREA.value)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    puntaje_maximo = db.Column(db.Float, nullable=False, default=100.0)
    porcentaje = db.Column(db.Float, nullable=False, default=10.0)  # peso sobre nota final
    materia_id = db.Column(db.Integer, db.ForeignKey('materias.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id'), nullable=False)
    cerrada = db.Column(db.Boolean, default=False)  # si está calificada por completo
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    notas = db.relationship('Nota', backref='evaluacion', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def total_calificadas(self):
        return self.notas.count()

    @property
    def promedio(self):
        notas = self.notas.all()
        if not notas:
            return 0.0
        return sum(n.puntaje for n in notas) / len(notas)

    def __repr__(self):
        return f'<Evaluacion {self.nombre} ({self.tipo})>'
