"""
Formularios WTForms para EduTrack.
"""
from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField, SelectField,
    TextAreaField, IntegerField, FloatField, DateField, EmailField, HiddenField
)
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, ValidationError, Optional,
    NumberRange, Regexp
)


class LoginForm(FlaskForm):
    username = StringField('Usuario o Email', validators=[DataRequired(), Length(min=3, max=120)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Mantener sesión iniciada')
    submit = SubmitField('Iniciar sesión')


class ResetPasswordRequestForm(FlaskForm):
    email = EmailField('Correo electrónico', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar restablecimiento')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva contraseña', validators=[
        DataRequired(), Length(min=6, message='Mínimo 6 caracteres')
    ])
    password2 = PasswordField('Confirmar contraseña', validators=[
        DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    submit = SubmitField('Cambiar contraseña')


class CambiarPasswordForm(FlaskForm):
    password_actual = PasswordField('Contraseña actual', validators=[DataRequired()])
    password_nueva = PasswordField('Nueva contraseña', validators=[
        DataRequired(), Length(min=6)
    ])
    password_nueva2 = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(), EqualTo('password_nueva')
    ])
    submit = SubmitField('Cambiar contraseña')


class ProfesorForm(FlaskForm):
    username = StringField('Usuario (dejar vacío para usar la cédula)',
                            validators=[Optional(), Length(min=3, max=80)])
    email = EmailField('Correo electrónico', validators=[DataRequired(), Email()])
    cedula = StringField('Cédula', validators=[DataRequired(), Length(max=30)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=80)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(max=80)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=30)])
    direccion = StringField('Dirección', validators=[Optional(), Length(max=255)])
    especialidad = StringField('Especialidad', validators=[Optional(), Length(max=100)])
    titulo = StringField('Título académico', validators=[Optional(), Length(max=150)])
    password = PasswordField('Contraseña (dejar vacío para no cambiar)',
                              validators=[Optional(), Length(min=6)])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')


class EstudianteForm(FlaskForm):
    codigo = StringField('Código estudiantil', validators=[DataRequired(), Length(max=30)])
    cedula = StringField('Cédula', validators=[Optional(), Length(max=30)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=80)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(max=80)])
    email = EmailField('Correo electrónico', validators=[Optional(), Email()])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=30)])
    fecha_nacimiento = DateField('Fecha de nacimiento', validators=[Optional()])
    direccion = StringField('Dirección', validators=[Optional(), Length(max=255)])
    seccion = StringField('Sección', validators=[Optional(), Length(max=50)])
    encargado = StringField('Nombre del encargado', validators=[Optional(), Length(max=150)])
    telefono_encargado = StringField('Teléfono encargado', validators=[Optional(), Length(max=30)])
    estado = SelectField('Estado', choices=[
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('graduado', 'Graduado'),
        ('retirado', 'Retirado'),
    ], default='activo')
    submit = SubmitField('Guardar')


class MateriaForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(), Length(max=20)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    creditos = IntegerField('Créditos', default=3, validators=[NumberRange(min=1, max=10)])
    horas_semana = IntegerField('Horas/semana', default=4, validators=[NumberRange(min=1, max=20)])
    activa = BooleanField('Activa', default=True)
    submit = SubmitField('Guardar')


class GrupoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(), Length(max=30)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    materia_id = SelectField('Materia', coerce=int, validators=[DataRequired()])
    profesor_id = SelectField('Profesor titular', coerce=int, validators=[DataRequired()])
    periodo = StringField('Periodo', validators=[DataRequired(), Length(max=20)], default='2026-I')
    anio = IntegerField('Año', validators=[NumberRange(min=2020, max=2100)], default=2026)
    cupo_maximo = IntegerField('Cupo máximo', validators=[NumberRange(min=1, max=200)], default=35)
    aula = StringField('Aula', validators=[Optional(), Length(max=50)])
    horario = StringField('Horario', validators=[Optional(), Length(max=120)])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')


class EvaluacionForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=150)])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    tipo = SelectField('Tipo', choices=[
        ('examen', 'Examen'),
        ('quiz', 'Quiz'),
        ('tarea', 'Tarea'),
        ('proyecto', 'Proyecto'),
        ('exposicion', 'Exposición'),
        ('practica', 'Práctica'),
        ('participacion', 'Participación'),
    ], validators=[DataRequired()])
    fecha = DateField('Fecha', validators=[DataRequired()], default=date.today)
    puntaje_maximo = FloatField('Puntaje máximo', validators=[
        DataRequired(), NumberRange(min=1, max=1000)
    ], default=100)
    porcentaje = FloatField('Porcentaje (%) sobre nota final', validators=[
        DataRequired(), NumberRange(min=0.1, max=100)
    ], default=10)
    grupo_id = SelectField('Grupo', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')


class AsignarMateriasForm(FlaskForm):
    """Form para asignar materias a un profesor."""
    materia_ids = HiddenField()
    submit = SubmitField('Guardar asignación')


class MatricularEstudianteForm(FlaskForm):
    """Form para matricular estudiantes en un grupo."""
    estudiante_ids = HiddenField()
    submit = SubmitField('Matricular')
