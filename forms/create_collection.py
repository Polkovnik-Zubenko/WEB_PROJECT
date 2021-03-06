from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired


class CreateCollection(FlaskForm):
    title = StringField('Введите название сборника', validators=[DataRequired()])
    password = PasswordField('Введите пароль для сборника задач')
    submit = SubmitField('Создать')
