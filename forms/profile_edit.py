from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, SelectField
from wtforms.validators import DataRequired


class Profile(FlaskForm):
    name_surname = StringField('Имя и фамилия пользователя', validators=[DataRequired()])
    country_city = StringField('Страна и город проживания пользователя', validators=[DataRequired()])
    nickname = StringField('Nickname:', validators=[DataRequired()])
    gender = StringField('Пол:', validators=[DataRequired()])
    school = StringField('Школа:')
    school_class = SelectField('Класс обучения пользователя',
                               choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                        ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
                                        ('11', '11')])
    year_finish_school = SelectField('Год выпуска пользователя',
                                     choices=[('2014', '2014'), ('2015', '2015'), ('2016', '2016'), ('2017', '2017'),
                                              ('2018', '2018'), ('2019', '2019'), ('2020', '2020'), ('2021', '2021'),
                                              ('2022', '2022'), ('2023', '2023'), ('2024', '2024'), ('2025', '2025'),
                                              ('2026', '2026'), ('2027', '2027')])
    submit = SubmitField('Подтверждение изменений')
