"""
Modelo Asistencia.
"""
from datetime import datetime, date
from enum import Enum
from app import db


class EstadoAsistenciaEnum(str, Enum):
    PRESENTE = 'presente'
    AUSENTE = 'ausente'
    JUSTIFICADO = 'justificado'
    TARDIA = 'tardia'


class Asistencia(db.Model):
    __tablename__ = 'asistencias'

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id', ondelete='CASCADE'),
                              nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id', ondelete='CASCADE'),
                         nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    estado = db.Column(db.String(20), nullable=False, default=EstadoAsistenciaEnum.PRESENTE.value)
    observaciones = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow,
                                     onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('estudiante_id', 'grupo_id', 'fecha', name='uq_asistencia_dia'),
        db.Index('idx_asistencia_grupo_fecha', 'grupo_id', 'fecha'),
    )

    def __repr__(self):
        return f'<Asistencia {self.estudiante_id} {self.fecha} {self.estado}>'
