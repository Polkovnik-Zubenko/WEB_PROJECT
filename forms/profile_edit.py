from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired


class Profile(FlaskForm):
    name_surname = StringField('Имя и фамилия пользователя', validators=[DataRequired()])
    country_city = StringField('Страна и город проживания пользователя', validators=[DataRequired()])
    nickname = StringField('Nickname пользователя', validators=[DataRequired()])
    gender = StringField('Пол пользователя', validators=[DataRequired()])
    submit = SubmitField('Подтверждение изменений')
