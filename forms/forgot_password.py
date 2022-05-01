from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired


class ForgotForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    submit = SubmitField('Напомнить пароль')
