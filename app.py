import os
import re
import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from files.db_session import create_session
import bcrypt
from flask import Flask, request, make_response, session, render_template, redirect, abort, redirect, url_for
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy

from files.db_session import SqlAlchemyBase
from forms.login import LoginForm
from forms.user import RegisterForm
from files import db_session
import datetime
from files.users import User
from email_send import send_email
from forms.forgot_password import ForgotForm
from forms.profile_edit import Profile

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init('db/db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=20)
basedir = os.path.abspath(os.path.dirname('static/img/profiles/'))
app.config['UPLOAD_FOLDER'] = basedir
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.query(User).filter(User.id == user_id).one_or_none()


@app.route('/')
def index():
    param = {}
    print(current_user.is_authenticated)
    return render_template('index.html', **param)


@app.errorhandler(404)
def error_404(err):
    print(err)
    return render_template('404.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('profile', id_user=current_user.id))
    elif form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            # session['user'] = user.id
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    form = ForgotForm()
    if form.validate_on_submit():
        send_email(str(form.email.data))
        return redirect('/')
    return render_template('forgot_email.html', form=form)


@app.route('/forgot_password/<secret_key>')
def func(secret_key):
    param = {}
    pass


@app.route('/register', methods=["GET", "POST"])
def register_obr():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        surname = form.surname.data
        nickname = form.nickname.data
        email = form.email.data
        country = form.country.data
        city = form.city.data
        gender = form.gender.data
        type_user = form.type_user.data
        school = form.school.data
        school_class = form.school_class.data
        year_finish_school = form.year_finish_school.data
        password1 = form.password.data

        email_check = r"^[-\w\.]+@([-\w]+\.)+[-\w]{2,4}$"
        password_check = [re.search(r"[a-z]", password1), re.search(r"[A-Z]", password1),
                          re.search(r"[0-9]", password1)]
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form, message="Пароли не совпадают")
        elif not all(password_check):
            return render_template('register.html', title='Регистрация', form=form, message="Пароль слишком простой")
        elif len(nickname) <= 4 or len(password1) <= 8:
            return render_template('register.html', title='Регистрация', form=form, message="Пароль слишком короткий")
        else:
            session = create_session()
            user_email = session.query(User).filter(User.email == form.email.data).first()
            if user_email:
                return render_template('register.html', title='Регистрация', form=form,
                                       message="Такой пользователь уже есть")
            elif re.match(email_check, email) is None:
                return render_template('register.html', title='Регистрация', form=form,
                                       message="Адрес почты не соответствует минимальным требованиям по оформлению")
            else:
                session1 = create_session()
                user_new = User(name=name, surname=surname, nickname=nickname, email=email, country=country, city=city,
                                gender=gender, type_user=type_user, school=school, school_class=school_class,
                                year_finish_school=year_finish_school, hashed_password=password1)
                user_new.set_password(password1)
                session1.add(user_new)
                session1.commit()
                return redirect('/login')
    return render_template('register.html', form=form)


@app.route('/profile/<int:id_user>')
@login_required
def profile(id_user):
    session2 = create_session()
    param = {}
    u = session2.query(User).filter(User.id == id_user).first()
    ava = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], f'{id_user}.png'))
    path = f'../static/img/profiles/{id_user}.png'
    if current_user.id == u.id:
        return render_template('profile.html', title=f'{u.nickname}', u=u, path=path)
    else:
        return redirect(url_for('register_page'))


@app.route('/profile-edit/<int:id_user>')
@login_required
def profile_edit(id_user):
    form = Profile()
    files_lst = os.listdir(basedir)
    db_sess = db_session.create_session()
    u = db_sess.query(User).filter(User.id == id_user).first()
    ava = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], f'{id_user}.png'))
    path = f'../static/img/profiles/{id_user}.png'
    if request.method == "GET":
        db_sess = db_session.create_session()
        u = db_sess.query(User).filter(User.id == id_user).first()
        if u:
            form.name_surname.data = f'{u.name} {u.surname}'
            form.country_city.data = f'{u.country} {u.city}'
            form.nickname.data = u.nickname
            form.gender.data = u.gender
            print(form.name_surname.data, form.country_city.data, form.nickname.data, form.gender.data)
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        u = db_sess.query(User).filter(User.id == id_user).first()
        if u:
            u.name = form.name_surname.data.split(' ')[0]
            u.surname = form.name_surname.data.split(' ')[1]
            u.country = form.country_city.data.split(" ")[0]
            u.city = form.country_city.data.split(" ")[1]
            u.nickname = form.nickname.data
            u.gender = form.gender.data
            print(u.name, u.surname, u.country, u.city, u.nickname, u.gender)
            db_sess.commit()
            return redirect('/profile')
        else:
            abort(404)
    return render_template('profile_edit.html', title=f'{u.nickname}', u=u, path=path)


@app.route('/path', methods=["POST", "GET"])
def upload_file():
    param = {}
    if request.method == "POST":
        file = request.files['file']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f'{current_user.id}.png'))
        return redirect(url_for('profile', id_user=current_user.id))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    app.run()


