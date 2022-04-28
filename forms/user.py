from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, RadioField, SelectField
# from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    surname = StringField('Фамилия пользователя', validators=[DataRequired()])
    nickname = StringField('Nickname пользователя', validators=[DataRequired()])
    email = EmailField('Электронная почта', validators=[DataRequired()])
    country = StringField('Страна проживания пользователя', validators=[DataRequired()])
    city = StringField('Город проживания пользователя', validators=[DataRequired()])
    gender = RadioField('Пол пользователя', choices=[('man', 'Мужской'), ('woman', 'Женский')])
    type_user = RadioField('Тип учетной записи', choices=[('student', 'Ученик'), ('teacher', 'Учитель')])
    school = StringField('Школа обучения пользователя')
    school_class = SelectField('Класс обучения пользователя', default='0',
                               choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                        ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
                                        ('11', '11')])
    year_finish_school = SelectField('Год выпуска пользователя', default='0',
                                     choices=[('2014', '2014'), ('2015', '2015'), ('2016', '2016'), ('2017', '2017'),
                                              ('2018', '2018'), ('2019', '2019'), ('2020', '2020'), ('2021', '2021'),
                                              ('2022', '2022'), ('2023', '2023'), ('2024', '2024'), ('2025', '2025'),
                                              ('2026', '2026'), ('2027', '2027')])

    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Подтверждение пароля', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')
