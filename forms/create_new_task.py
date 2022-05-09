from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, FileField
from wtforms.validators import DataRequired


class CreateTask(FlaskForm):
    title = StringField('Введите название задачи', validators=[DataRequired()])
    discription = TextAreaField('Введите условие задачи', validators=[DataRequired()])
    input = FileField('Введите входные данные для первого теста', validators=[DataRequired()])
    output = FileField('Введите выходные данные для первого теста', validators=[DataRequired()])
    tests = FileField(validators=[DataRequired()])
    submit = SubmitField('Создать')
