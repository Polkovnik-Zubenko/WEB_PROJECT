from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, RadioField, SelectField
# from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class RecoveryPassword(FlaskForm):
    old_password = PasswordField('Введите старый пароль:', validators=[DataRequired()])
    password = PasswordField('Введите новый пароль', validators=[DataRequired()])
    password_again = PasswordField('Подтверждение нового пароля', validators=[DataRequired()])
    submit = SubmitField('Обновить пароль')
