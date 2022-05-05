from base64 import encode
import glob
import os
import re
import datetime
import subprocess
import random

import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from files.db_session import create_session
import bcrypt
from flask import Flask, request, make_response, session, render_template, redirect, abort, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy

from files.db_session import SqlAlchemyBase
from files.new_password import Password
from files.tasks import Task
from forms.login import LoginForm
from forms.user import RegisterForm
from files import db_session
import datetime
from files.users import User
from email_send import send_email
from forms.forgot_password import ForgotForm
from forms.profile_edit import Profile
from forms.profile_new_password import RecoveryPassword
from email_send import create_secret_key

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init('db/db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=20)
basedir = os.path.abspath(os.path.dirname('static/img/profiles/'))
solutdir = os.path.abspath(os.path.dirname('static/solutions/'))
app.config['UPLOAD_FOLDER'] = [basedir, solutdir]
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

#  drimilya2018@gmail.com
#  nolifecat12345_ZA

@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.query(User).filter(User.id == user_id).one_or_none()


@app.route('/')
def index():
    param = {}
    if current_user.is_authenticated:
        files_lst = os.listdir(basedir)
        key = f'{current_user.id}' + '.png'
        path = f'/static/img/profiles/{current_user.id}.png'
        param['files_lst'] = files_lst
        param['key'] = key
        param['path'] = path
        return render_template('index.html', **param)
    return render_template('index.html')


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
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    form = ForgotForm()
    if form.validate_on_submit():
        key = create_secret_key()
        send_email(str(form.email.data), key)
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        lst = ''
        try:
            lst = user.id
        except Exception:
            pass
        if lst:
            password = Password(key=key, user_id=user.id)
            db_sess2 = create_session()
            db_sess2.add(password)
            db_sess2.commit()
        else:
            return render_template('forgot_email.html', form=form, message="Вы не зарегистрированы в системе")

        return redirect('/')
    return render_template('forgot_email.html', form=form)


@app.route('/forgot_password/<secret_key>')
def forgot_password2(secret_key):
    db_sess = create_session()
    user = db_sess.query(Password).filter(Password.key == secret_key).first()
    print(user.user_id)
    return render_template('recovery-password.html')


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
        elif len(password1) <= 8:
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
    files_lst = os.listdir(basedir)
    key = f'{id_user}' + '.png'
    u = session2.query(User).filter(User.id == id_user).first()
    ava = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'][0], f'{id_user}.png'))
    path = f'/static/img/profiles/{id_user}.png'
    if current_user.id == u.id:
        return render_template('profile.html', title=f'{u.nickname}', u=u, path=path, files_lst=files_lst, key=key)
    else:
        return redirect(url_for('register_page'))


@app.route('/profile-edit/<int:id_user>')
@login_required
def profile_edit(id_user):
    form = Profile()
    files_lst = os.listdir(basedir)
    key = f'{id_user}' + '.png'
    db_sess = db_session.create_session()
    u = db_sess.query(User).filter(User.id == id_user).first()
    ava = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'][0], f'{id_user}.png'))
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
    print(form.validate_on_submit())
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
    return render_template('profile_edit.html', title=f'{u.nickname}', u=u, path=path, files_lst=files_lst, key=key,
                           form=form)


@app.route('/recovery-password/<int:id_user>')
@login_required
def recovery_password(id_user):
    form = RecoveryPassword()
    session2 = create_session()
    files_lst = os.listdir(basedir)
    key = f'{id_user}' + '.png'
    u = session2.query(User).filter(User.id == id_user).first()
    path = f'/static/img/profiles/{id_user}.png'
    password_check = [re.search(r"[a-z]", str(form.password.data)), re.search(r"[A-Z]", str(form.password.data)),
                      re.search(r"[0-9]", str(form.password.data))]
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if user and user.check_password(form.old_password.data):
            if form.password.data != form.password_again.data:
                return render_template('recovery-password.html', title='Восстановление пароля', form=form,
                                       message="Пароли не совпадают")
            elif form.old_password.data == form.password.data:
                return render_template('recovery-password.html', title='Восстановление пароля', form=form,
                                       message="Новый пароль совпадает со старым")
            elif not all(password_check):
                return render_template('recovery-password.html', title='Восстановление пароля', form=form,
                                       message="Пароль слишком простой")
            elif len(form.password.data) <= 8:
                return render_template('recovery-password.html', title='Восстановление пароля', form=form,
                                       message="Пароль слишком короткий")
            else:
                session1 = create_session()
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                user.hashed_password = form.password.data
                session1.commit()
                return render_template('recovery-password.html', title='Восстановление пароля', form=form,
                                       message="Пароль был успешно изменён!")
        return render_template('recovery-password.html', message="Неправильный пароль", form=form)
    return render_template('recovery-password.html', title='Восстановление пароля', u=u, path=path, files_lst=files_lst,
                           key=key, form=form)


@app.route('/path', methods=["POST", "GET"])
def upload_file():
    if request.method == "POST":
        id = request.form['id']
        if id == '0':
            file = request.files['file']
            file.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][0]}", f'{current_user.id}.png'))
            return redirect(url_for('profile', id_user=current_user.id))
        else:
            file = request.files['solut']
            file.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][1]}", 'solution.py'))

            path_file = 'static/solutions/solution.py'
            path = f'static/tests/{id}'
            otv = 'OK'

            for test in range(len(glob.glob(f'{path}/*')) // 2):
                if len(str(test)) == 1:
                    test = f'0{test + 1}'
                else:
                    test = f'{test + 1}'
                with open(f"{path}/{test}") as input_:
                    input_ = input_.readlines()
                    input_ = [line.rstrip() for line in input_]
                p = subprocess.Popen(f'python {path_file}', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     encoding='utf-8',
                                     stdin=subprocess.PIPE)  # запуск файла
                for i in input_:  # передача данных в файл
                    p.stdin.write(f'{i}\n')
                with open(f'{path}/{test}.a') as output_:
                    output_ = output_.readlines()
                    output_ = [line.rstrip() for line in output_]
                output_program, error = p.communicate()
                if output_ == output_program.split('\n')[:-1]:
                    pass
                elif error:
                    otv = f'Ошибка в тесте: {test}+{error}'
                    break
                else:
                    otv = f'Ошибка в тесте: {test}'
                    break
            flash(otv)
            return redirect(url_for('task_page', id_task=id))


@app.route('/task/<int:id_task>')
def task_page(id_task):
    db_sess = create_session()
    t = db_sess.query(Task).filter(Task.id == id_task).first()
    return render_template('task_template.html', t=t)


@app.route('/tasks')
def tasks():
    db_sess = create_session()
    t = db_sess.query(Task).all()
    return render_template('tasks.html', t=t)


@app.route('/create-test')
@login_required
def create_test():
    db_sess = create_session()
    t = db_sess.query(Task).all()
    return render_template('create_test.html', t=t)


@app.route('/create_test_for_user', methods=["POST"])
def create_test_for_user():
    flag = False
    id_tests = request.form['tests']
    db_sess = create_session()
    id_tests = id_tests.split(', ')
    for i in id_tests:
        if db_sess.query(Task).filter(Task.id == i).first():
            flag = True
        else:
            flag = False
    if current_user.is_authenticated and flag:
        id_user = current_user.id
        path_to_test = f'/created-test-{id_user}/{random.randint(0, 10000000)}\n'
        if os.path.exists(f'static/created_tests/created-test{id_user}.txt'):
            f = open(f'static/created_tests/created-test{id_user}.txt', mode='a')
            for i in id_tests:
                print(i)
                f.write(i + ',')
            f.write(' ')
            f.write(path_to_test)
            f.close()
        else:
            f = open(f'static/created_tests/created-test{id_user}.txt', mode='w')
            for i in id_tests:
                print(i)
                f.write(i + ',')
            f.write(' ')
            f.write(path_to_test)
            f.close()
    if flag:
        flash(path_to_test)
    else:
        flash('Вы ввели задачи не так')
    return redirect(url_for('create_test'))


@app.route('/created-test-<int:id_teacher>/<int:id_test>')
@login_required
def created_test_teach(id_teacher, id_test):
    if os.path.exists(f'static/created_tests/created-test{id_teacher}.txt'):
        f = open(f'static/created_tests/created-test{id_teacher}.txt', mode='r')
        f = [line.strip() for line in f]
        for i in f:
            tmp = i.split(' ')
            if f'/created-test-{id_teacher}/{id_test}' in tmp:
                zadachi = tmp[0].split(',')[:-1]
        return render_template('created_test.html', title=id_test, zadachi=zadachi)
    else:
        return redirect(url_for('error_404'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    app.run()
