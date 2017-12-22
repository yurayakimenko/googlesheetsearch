from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

app = Flask(__name__)
app.debug = True
scope =['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('product_spreadsheets.json', scope)
client = gspread.authorize(creds)

import configparser
config = configparser.ConfigParser()
config.read('config/telebot_config.ini')

app.config['MYSQL_HOST'] = config['BOT']['host']
app.config['MYSQL_USER'] = config['BOT']['user']
app.config['MYSQL_PASSWORD'] = config['BOT']['passwd']
app.config['MYSQL_DB'] = config['BOT']['db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

app.static_folder = 'static'

@app.route('/')
def index():
    return render_template('home.html')

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        cur = mysql.connection.cursor()
        result_user = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        result_email = cur.execute("SELECT * FROM users WHERE email = %s", [email])
        if result_user == 0 and result_email == 0:
            cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
            mysql.connection.commit()
            cur.close()
            flash('Вы зарегестрированны и можете войти.', 'success')
            redirect(url_for('index'))
        elif result_user > 0:
            flash('Пользователь с таким ником уже зарегестрирован.', 'danger')
        elif result_email > 0:
            flash('Этот адресс уже зарегестрирован.', 'danger')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash('Вы успешно вошли.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Неправильный пароль.', 'danger')
            cur.close()
        else:
            flash('Нет такого пользователя.', 'danger')
    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Неавторизированный вход.', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли.', 'success')
    return redirect(url_for('login'))

def searchsheets():
    products = []
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM customers")
    tables = cur.fetchall()
    tablenames = [i['tablename'] for i in tables]
    names = [i['name'] for i in tables]
    for tablename , name in zip(tablenames, names):
        try:
            searchobject = client.open(tablename).sheet1
            search = request.form['search']
            regular = re.escape(search)
            criteria_re = re.compile(regular)
            cells = searchobject.findall(criteria_re)
            for cell in cells:
                appending = searchobject.row_values(cell.row)
                appending.insert(0, name)
                products.append(appending)
        except:
            continue
    return products

@app.route('/search', methods = ['GET', 'POST'])
@login_required
def search():
    products = []
    customers = []
    if request.method == 'POST':
        products = searchsheets()
    return render_template('search.html', products = products)

@app.route('/dashboard', methods =['GET', 'POST'])
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM checklist")
    checklist = cur.fetchall()
    if request.method == 'POST':
        add_search = request.form['add_search']
        cur.execute("INSERT INTO checklist(searchrequest) VALUES(%s)", [add_search])
        mysql.connection.commit()
        cur.close()
        flash('Новый поисковый запрос добавлен.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', checklist=checklist)

@app.route('/customers')
@login_required
def customers():
    flash('Обязательно добавьте этот адрес в те, которые имеют доступ к таблице поставщика. Google Таблицы > Настройки доступа.', 'warning')
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    return render_template('customers.html', customers = customers)

@app.route('/add_customer', methods =['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        tablename = request.form['tablename']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO customers (name, tablename) VALUES(%s, %s)", (name, tablename))
        mysql.connection.commit()
        cur.close()
        flash('Поставщик добавлен!', 'success')
        return redirect(url_for('customers'))
    return render_template('add_customer.html')

@app.route(u'/delete_search/<string:id>', methods = ['POST'])
@login_required
def delete_search(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM checklist WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Поисковый запрос удалён', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_customer/<string:name>', methods = ['POST'])
@login_required
def delete_customer(name):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM customers WHERE name = %s", [name])
    mysql.connection.commit()
    cur.close()
    flash('Поставщик удалён', 'success')
    return redirect(url_for('customers'))

@app.route(u'/add_search/<string:id>', methods = ['POST'])
@login_required
def add_search_by(id):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO checklist(searchrequest) VALUES(%s)", [id])
    mysql.connection.commit()
    cur.close()
    flash('Новый поисковый запрос добавлен.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_bot', methods = ['POST'])
@login_required
def add_bot():
    import configparser
    config = configparser.ConfigParser()
    config.read('config/telebot_config.ini')
    config['BOT'] = {'TOKEN': request.form['add_bot']}
    with open('telebot_config.ini', 'w') as configfile:
        config.write(configfile)
    flash('Новый токен добавлен.', 'success')
    return redirect(url_for('bot_state'))

if __name__ == '__main__':
    app.secret_key='secret'
    app.run()
