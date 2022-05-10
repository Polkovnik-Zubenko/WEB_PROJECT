from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired


class HelpForm(FlaskForm):
    topic = StringField('Введите тему письма', validators=[DataRequired()])
    text = TextAreaField('Введите сообщение по заданной теме')
    submit = SubmitField('Отправить письмо')
