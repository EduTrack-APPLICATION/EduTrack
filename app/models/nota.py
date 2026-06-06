"""
Modelo Nota: una nota es la calificación de un estudiante en una evaluación.
"""
from datetime import datetime
from app import db


class Nota(db.Model):
    __tablename__ = 'notas'

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id', ondelete='CASCADE'),
                              nullable=False)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id', ondelete='CASCADE'),
                              nullable=False)
    puntaje = db.Column(db.Float, nullable=False, default=0.0)
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('estudiante_id', 'evaluacion_id', name='uq_estudiante_evaluacion'),
        db.CheckConstraint('puntaje >= 0', name='ck_puntaje_no_negativo'),
    )

    @property
    def porcentaje_obtenido(self):
        """Retorna el % del puntaje sobre el máximo."""
        if not self.evaluacion or self.evaluacion.puntaje_maximo == 0:
            return 0
        return (self.puntaje / self.evaluacion.puntaje_maximo) * 100

    @property
    def aporte_nota_final(self):
        """Aporte ponderado a la nota final."""
        return self.porcentaje_obtenido * (self.evaluacion.porcentaje / 100)

    def __repr__(self):
        return f'<Nota est={self.estudiante_id} eval={self.evaluacion_id} {self.puntaje}>'
