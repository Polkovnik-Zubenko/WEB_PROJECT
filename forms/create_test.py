from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired


class CreateTest(FlaskForm):
    number = StringField('Введите № задачи', validators=[DataRequired()])
    submit = SubmitField('Перейти')
