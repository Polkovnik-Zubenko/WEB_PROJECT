from doctest import testmod
from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import re
import os
from werkzeug.utils import secure_filename
import subprocess
import glob

app = Flask(__name__)
app.config['SECRET_KEY'] ='super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yandex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
basedir = os.path.abspath(os.path.dirname('static/img/profiles/'))
solutdir = os.path.abspath(os.path.dirname('static/solutions/'))
app.config['UPLOAD_FOLDER'] = [basedir, solutdir]
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    surname = db.Column(db.Text, nullable=False)
    nickname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.id

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text, nullable=False)
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text, nullable=False)


@app.route('/')
def register_page():
    otv = ''
    user = User.query.get(session.get('user'))
    if 'user' in session:
        otv = 'Вы авторизованы'
    return render_template('register_page.html', title='Регистрация', otv=otv)


@app.route('/login')
def login_page():
    if session.get('user'):
        return redirect(url_for('profile', id_user=session.get('user')))
    return render_template('login_page.html')


@app.route('/login-obr', methods=['POST'])
def login_obr():
    otv = ''
    login = request.form['login']
    pass1 = request.form['password']
    user = User.query.filter_by(nickname=login).first()
    if user:
        password_check_valid = bcrypt.checkpw(pass1.encode(), user.password)
        if password_check_valid:
            session['user'] = user.id
        else:
            otv = "Неверное имя пользователя или пароль"
    else:
        otv = "Неверное имя пользователя или пароль"
    if otv:
        return render_template('login_page.html', otv=otv)
    else:
        return redirect(url_for('profile', id_user=user.id))
        

@app.route('/register-obr', methods=['POST'])
def register_obr():
    otv = ''
    name = request.form['name']
    surname = request.form['surname']
    email = request.form['email']
    nickname = request.form['nickname']
    password1 = request.form['password1']
    password2 = request.form['password2']

    mail_check = r"^[-\w\.]+@([-\w]+\.)+[-\w]{2,4}$"
    password_check = [re.search(r"[a-z]", password1), re.search(r"[A-Z]", password1), re.search(r"[0-9]", password1), re.search(r"\W", password1)]
    if all(password_check):
        pass
    else:
        otv = 'Ошибка регистрации1'

    if name != '' and surname != '' and email != '' and nickname != '' and password1 != '' and password2 != '':
        if len(nickname) <= 4 or len(password1) < 8:
            otv = 'Ошибка регистрации2'
        else:
            user_nick = User.query.filter(User.nickname==nickname).first()
            user_mail = User.query.filter(User.mail==email).first()
            if user_nick:
                if user_nick.nickname == nickname:
                    otv = 'Ошибка регистрации3'
            elif user_mail:
                if user_mail.mail == email:
                    otv = "Ошибка регистрации4"
            elif password1 != password2:
                otv = 'Ошибка регистрации5'
            elif re.match(mail_check, email) is None:
                otv = 'Ошибка регистрации6'
            else:
                if otv == "Ошибка регистрации7":
                    pass
                else: 
                    password_hashed = bcrypt.hashpw(password1.encode(), bcrypt.gensalt())
                    user_new = User(mail = email, name=name, surname=surname, nickname=nickname, password=password_hashed)
                    db.session.add(user_new)
                    db.session.commit()
                    otv = 'Успешная регистрация'
    else:
        otv = 'Ошибка регистрации'

    return render_template('proverka.html', otv=otv)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('register_page'))


@app.route('/profile/<int:id_user>')
def profile(id_user):
    u = User.query.filter(User.id == id_user).first()
    ava = os.path.exists(os.path.join(f"{app.config['UPLOAD_FOLDER'][0]}", f'{id_user}.png'))
    path = f'../static/img/profiles/{id_user}.png'
    if session.get('user') == u.id:
        return render_template('profile.html', title=f'{u.nickname}', u=u, path=path)
    else:
        return redirect(url_for('register_page'))


@app.route('/profile-edit/<int:id_user>')
def profile_edit(id_user):
    u = User.query.filter(User.id == id_user).first()
    ava = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], f'{id_user}.png'))
    path = f'../static/img/profiles/{id_user}.png'
    return render_template('profile_edit.html', title=f'{u.nickname}', u=u, path=path)


@app.route('/edit-profile', methods=["POST"])
def edit_profile_data():
    pass

@app.route('/path', methods=["POST", "GET"])
def upload_file():
    if request.method == "POST":
        id =  request.form['id']
        if id == '0':
            file = request.files['file']
            file.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][0]}", f'{session.get("user")}.png'))
            return redirect(url_for('profile', id_user=session.get('user')))
        else:
            file = request.files['solut']
            file.save(os.path.join(f"{app.config['UPLOAD_FOLDER'][1]}", 'solution.py'))

            path_file = 'static/solutions/solution.py'
            path = f'static/tests/{id}'
            otv = 'Все нормально'

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



@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/task/<int:id_task>')
def task_page(id_task):
    t = Task.query.filter(Task.id == id_task).first()
    return render_template('task_template.html', t=t)


@app.route('/tasks')
def tasks():
    t = Task.query.all()
    return render_template('tasks.html', t=t)


if __name__ == "__main__":
    app.run(debug=True)
