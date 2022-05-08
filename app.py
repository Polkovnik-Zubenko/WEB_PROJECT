from base64 import encode
import glob
import os
import re
import datetime
import subprocess
import random
from zipfile import ZipFile
import shutil

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
from forms.profile_edit import ProfileEdit
from forms.profile_new_password import RecoveryPassword
from email_send import create_secret_key
from forms.recovery_password import RecoveryPassword2
from forms.number_task import NumberTask

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init('db/db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=20)
basedir = os.path.abspath(os.path.dirname('static/img/profiles/'))
solutdir = os.path.abspath(os.path.dirname('static/solutions/'))
newtaskdir = os.path.abspath(os.path.dirname('static/tmp_files/'))
app.config['UPLOAD_FOLDER'] = [basedir, solutdir, newtaskdir]
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.query(User).filter(User.id == user_id).one_or_none()


@app.route('/', methods=["GET", "POST"])
def index():
    form = NumberTask(csv=False)
    param = {}
    print(form.validate_on_submit())
    if form.validate_on_submit():
        return task_page(form.number.data)
    if current_user.is_authenticated:
        files_lst = os.listdir(basedir)
        key = f'{current_user.id}' + '.png'
        path = f'/static/img/profiles/{current_user.id}.png'
        param['files_lst'] = files_lst
        param['key'] = key
        param['path'] = path
        return render_template('index.html', form=form, **param)
    return render_template('index.html', form=form, **param)


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
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).one_or_none()
        if user:
            password = db_sess.query(Password).filter(Password.user_id == user.id).one_or_none()
            if password:
                password.key = key
            else:
                password = Password(key=key, user_id=user.id)
                db_sess.add(password)
            db_sess.commit()
        else:
            return render_template('forgot_email.html', form=form, message="Данный email не зарегистрирован в системе")

        send_email(str(form.email.data), key)

        return redirect('/')
    return render_template('forgot_email.html', form=form)


@app.route('/forgot_password/<secret_key>', methods=["GET", "POST"])
def forgot_password2(secret_key):
    form = RecoveryPassword2()
    form2 = ForgotForm()
    db_sess = create_session()
    similar = db_sess.query(Password).filter(Password.key == secret_key).one_or_none()
    if similar:
        if form.validate_on_submit():
            user_id = db_sess.query(Password.user_id).filter(Password.key == secret_key).first()
            print(123, user_id)
            user = db_sess.query(User).filter(User.id == user_id[0]).first()

            password_check = [re.search(r"[a-z]", str(form.password.data)),
                              re.search(r"[A-Z]", str(form.password.data)),
                              re.search(r"[0-9]", str(form.password.data))]
            if form.password.data != form.password_again.data:
                return render_template('recovery-password2.html', title='Восстановление пароля', form=form,
                                       message="Пароли не совпадают")
            elif user.check_password(form.password.data):
                return render_template('recovery-password2.html', title='Восстановление пароля', form=form,
                                       message="Новый пароль совпадает со старым")
            elif not all(password_check):
                return render_template('recovery-password2.html', title='Восстановление пароля', form=form,
                                       message="Пароль слишком простой")
            elif len(form.password.data) <= 8:
                return render_template('recovery-password2.html', title='Восстановление пароля', form=form,
                                       message="Пароль слишком короткий")
            else:
                user.set_password(form.password.data)
                db_sess.commit()
                return redirect('/')
        return render_template('recovery-password2.html', form=form)
    else:
        return render_template('forgot_email.html', form=form2,
                               message="Данная ссылка недействительна. Запросите восстановление пароля ещё раз.")


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


@app.route('/profile-edit/<int:id_user>', methods=["GET", "POST"])
@login_required
def profile_edit(id_user):
    form = ProfileEdit()
    files_lst = os.listdir(basedir)
    key = f'{id_user}' + '.png'
    db_sess = create_session()
    u = db_sess.query(User).filter(User.id == id_user).first()
    ava = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'][0], f'{id_user}.png'))
    path = f'../static/img/profiles/{id_user}.png'
    if request.method == "GET":
        db_sess = create_session()
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
        print(form.name_surname.data, form.country_city.data, form.nickname.data, form.gender.data, '__________')
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


@app.route('/recovery-password/<int:id_user>', methods=["GET", "POST"])
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
    print(form.validate_on_submit())
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if user:
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
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                user.set_password(form.password.data)
                db_sess.commit()
                return redirect('/')
                # return render_template('recovery-password.html', title='Восстановление пароля', form=form,
                #                        message="Пароль был успешно изменён!")
        return render_template('recovery-password.html', message="Неправильный пароль", form=form)
    return render_template('recovery-password.html', title='Восстановление пароля', u=u, path=path, files_lst=files_lst,
                           key=key, form=form)


@app.route('/about_team', methods=["POST", "GET"])
def about_team():
    if current_user.is_authenticated:
        files_lst = os.listdir(basedir)
        key = f'{current_user.id}' + '.png'
        path = f'/static/img/profiles/{current_user.id}.png'
        return render_template('team_project.html', path=path, files_lst=files_lst, key=key)
    else:
        return render_template('team_project.html')


@app.route('/path', methods=["POST", "GET"])
def upload_file():
    if request.method == "POST":
        id = request.form['id']
        if id == '0':
            file = request.files['file']
            file.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][0]}", f'{current_user.id}.png'))
            return redirect(url_for('profile', id_user=current_user.id))
        elif id == 'zip':
            file = request.files['file']
            file.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][2]}", f'{current_user.id}.zip'))

            db_sess = create_session()
            t = db_sess.query(Task).order_by(Task.id.desc()).first()

            myzip = ZipFile(f'static/tmp_files/{current_user.id}.zip')
            myzip.extractall(f'static/tmp_files/{current_user.id}')
            myzip.close()

            get_files = os.listdir(f'static/tmp_files/{current_user.id}/tests')
            os.mkdir(f'static/tests/{t.id + 1}')
            for g in get_files:
                os.mkdir(f'static/tests/{t.id + 1}/{g}')
                for file in os.listdir(f'static/tmp_files/{current_user.id}/tests/{g}'):
                    os.replace(f'static/tmp_files/{current_user.id}/tests/{g}/' + file,
                               f'static/tests/{t.id + 1}/{g}/' + file)

            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), f'static/tmp_files/{current_user.id}')
            shutil.rmtree(path)
            os.remove(f'static/tmp_files/{current_user.id}.zip')

            name_task = request.form['name']
            text_task = request.form['text-task']
            input_data = request.files['input_data']
            input_data.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][2]}", f'input-{current_user.id}.txt'))
            output_data = request.files['output_data']
            output_data.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][2]}", f'output-{current_user.id}.txt'))

            input_data_str = create_data_for_task(f'static/tmp_files/input-{current_user.id}.txt')
            output_data_str = create_data_for_task(f'static/tmp_files/output-{current_user.id}.txt')

            task_new = Task(name=name_task, text=text_task, input_text=input_data_str, output_text=output_data_str)
            db_sess.add(task_new)
            db_sess.commit()

            os.remove(f'static/tmp_files/input-{current_user.id}.txt')
            os.remove(f'static/tmp_files/output-{current_user.id}.txt')

            return redirect('/')
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


def create_data_for_task(name_file):
    with open(name_file) as f:
        str_mod = ''
        f = f.readlines()
        f = [line.rstrip() for line in f]
        for i in f:
            str_mod = str_mod + f'{i}<br>'
    return str_mod


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
        return abort(404)


@app.route('/create-new-task')
def create_new_task():
    return render_template('create_new_task.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    app.run()
