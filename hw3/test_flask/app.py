from werkzeug.security import generate_password_hash, check_password_hash

import pdfkit
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

from flask import send_file

import os

from form import Form
from storage import get_db, init_db, connect_db

app = Flask(__name__)

app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'))
init_db(app, app.config['DATABASE'])

print('XXX', app.config)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()


@app.route("/")
def index():
    return render_template("layout.html")


@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name="noname"):
    if session.get('logged_in'):
        name = session['username']
    return render_template('hello.html', name=name)


@app.route('/forms', methods=['GET', 'POST'])
def show_forms():
    if not session.get('logged_in'):
        abort(401)

    db = get_db(app.config['DATABASE'])
    author = session['username']
    query = f'select * from forms where user = \'{author}\' order by id desc'
    cur = db.execute(query)
    form = cur.fetchone()

    return render_template('form.html', form=form)


@app.route('/edit_form', methods=['POST'])
def add_form():
    if not session.get('logged_in'):
        abort(401)
    print(app.config)
    if "save" in request.form:
        db = get_db(app.config['DATABASE'])
        user = session['username']
        db.execute(
            'insert into forms (user, first_name, last_name, date_of_birth, email, education, skills, favourite_color) values (?, ?, ?, ?, ?, ?, ?, ?)',
            [user, request.form['name1'], request.form['name2'],
             request.form['birth_date'], request.form['email'],
             request.form['education'], request.form['skills'],
             request.form['color']
             ]
        )
        db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_forms'))

    form = Form(first_name=request.form['name1'],
                last_name=request.form['name2'],
                date_of_birth=request.form['birth_date'],
                email=request.form['email'],
                education=request.form['education'],
                skills=request.form['skills'],
                favourite_color=request.form['color'],
                )
    return redirect(url_for('download', form=form))


@app.route('/download/<form>', methods=['GET', 'POST'])
def download(form):
    form = eval(form)
    s = render_template('form.html', form=form)
    s = s[:s.rfind('\n')]
    pdfkit.from_string(s,
                       'file.pdf')
    return send_file(path_or_file='file.pdf',
                     download_name='info.pdf',
                     as_attachment=True)


@app.route('/thoughts', methods=['GET', 'POST'])
def show_thoughts():
    if not session.get('logged_in'):
        abort(401)

    db = get_db(app.config['DATABASE'])
    author = session['username']
    query = f'select text,created_at from entries where author = \'{author}\' order by id desc'
    cur = db.execute(query)
    thoughts = cur.fetchall()
    return render_template('thoughts.html', thoughts=thoughts)


@app.route('/add', methods=['POST'])
def add_thought():
    if not session.get('logged_in'):
        abort(401)
    print(app.config)
    db = get_db(app.config['DATABASE'])
    author = session['username']
    db.execute(
        'insert into entries (text, author) values (?, ?)',
        [request.form['text'], author]
    )
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_thoughts'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_db(app.config['DATABASE'])
        username = request.form['username']
        password = request.form['password']

        query = f'select username,password from users where username = \'{username}\''
        cur = db.execute(query)
        user = cur.fetchone()
        if not user:
            error = f'No such user {username}'
        elif not check_password_hash(user['password'], password):
            error = f'Wrong password'
        else:
            session['username'] = username
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('hello'))

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        db = get_db(app.config['DATABASE'])
        username = request.form['username']
        password = request.form['password']

        query = f'select username,password from users where username = \'{username}\''
        cur = db.execute(query)
        user = cur.fetchone()
        if user:
            error = f'User {username} already exists'
        elif not password:
            error = f'Password required'
        else:
            db.execute(
                'insert into users (username, password) values (?, ?)',
                [username, generate_password_hash(password)]
            )
            db.commit()
            flash('New user was successfully registered')
            session['username'] = username
            session['logged_in'] = True
            return redirect(url_for('hello'))

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    # удалить из сессии имя пользователя, если оно там есть
    session.pop('username', None)
    session['logged_in'] = False
    flash('You were logged out')
    return redirect(url_for('login'))


app.run(debug=True, port=8888)
