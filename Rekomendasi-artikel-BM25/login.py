# from flask import Flask, render_template, redirect, url_for, request, flash
# from flask_mysqldb import MySQL
# from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, SubmitField
# from werkzeug.security import generate_password_hash, check_password_hash
# from wtforms.validators import DataRequired

# app = Flask(__name__)

# app.config['SECRET_KEY'] = 'victor14'
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_PORT'] = 3306
# app.config['MYSQL_DB'] = 'rekomendasi_bm25'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# mysql = MySQL(app)
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'

# class LoginForm(FlaskForm):
#     npm = StringField('NPM', [DataRequired()])
#     password = PasswordField('Password', [DataRequired()])
#     submit = SubmitField('Login')

# class LoginFormAdmin(FlaskForm):
#     nama = StringField('Nama', [DataRequired()])
#     password = PasswordField('Password', [DataRequired()])
#     submit = SubmitField('Login')

# class SignupForm(FlaskForm):
#     nama = StringField('Nama', [DataRequired()])
#     npm = StringField('NPM', [DataRequired()])
#     password = PasswordField('Password', [DataRequired()])
#     submit = SubmitField('Signup')

# class SignupFormAdmin(FlaskForm):
#     nama = StringField('Nama', [DataRequired()])
#     password = PasswordField('Password', [DataRequired()])
#     submit = SubmitField('Signup')

# class User(UserMixin):
#     def __init__(self, id, nama, npm, password):
#         self.id = id
#         self.nama = nama
#         self.npm = npm
#         self.password = password
        
# class Admin(UserMixin):
#     def __init__(self, id, nama, password):
#         self.id = id
#         self.nama = nama
#         self.password = password

# @login_manager.user_loader
# def load_user(user_id):
#     cur = mysql.connection.cursor()
#     # Check in pengguna table
#     cur.execute("SELECT * FROM pengguna WHERE id = %s", (user_id,))
#     user_data = cur.fetchone()
#     if user_data:
#         cur.close()
#         return User(id=user_data['id'], nama=user_data['nama'], npm=user_data['npm'], password=user_data['password'])
    
#     # Check in admin table
#     cur.execute("SELECT * FROM admin WHERE id = %s", (user_id,))
#     admin_data = cur.fetchone()
#     cur.close()
#     if admin_data:
#         return Admin(id=admin_data['id'], nama=admin_data['nama'], password=admin_data['password'])
#     return None

# @app.route('/')
# def home():
#     return redirect(url_for('signupadmin'))

# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     form = SignupForm()
#     if form.validate_on_submit():
#         hashed_password = generate_password_hash(form.password.data)
#         cur = mysql.connection.cursor()
#         cur.execute("INSERT INTO pengguna (nama, npm, password) VALUES (%s, %s, %s)", (form.nama.data, form.npm.data, hashed_password))
#         mysql.connection.commit()
#         cur.close()
#         flash('Signed up successfully!', 'success')
#         return redirect(url_for('login'))
#     return render_template('signup.html', form=form)

# @app.route('/signupadmin', methods=['GET', 'POST'])
# def signupadmin():
#     form = SignupFormAdmin()
#     if form.validate_on_submit():
#         hashed_password = generate_password_hash(form.password.data)
#         cur = mysql.connection.cursor()
#         cur.execute("INSERT INTO admin (nama, password) VALUES (%s, %s)", (form.nama.data, hashed_password))
#         mysql.connection.commit()
#         cur.close()
#         flash('Signed up successfully!', 'success')
#         return redirect(url_for('login_admin'))
#     return render_template('signup_admin.html', form=form)

# @app.route('/login_admin', methods=['GET', 'POST'])
# def login_admin():
#     form = LoginFormAdmin()
#     if form.validate_on_submit():
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM admin WHERE nama = %s", (form.nama.data,))
#         user_data = cur.fetchone()
#         cur.close()
#         if user_data and check_password_hash(user_data['password'], form.password.data):
#             user = Admin(id=user_data['id'], nama=user_data['nama'], password=user_data['password'])
#             login_user(user)
#             return redirect(url_for('dashboard'))
#         flash('Login Unsuccessful. Check nama and password', 'danger')
#     return render_template('login_admin.html', form=form)


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM pengguna WHERE npm = %s", (form.npm.data,))
#         user_data = cur.fetchone()
#         cur.close()
#         if user_data and check_password_hash(user_data['password'], form.password.data):
#             user = User(id=user_data['id'], nama=user_data['nama'], npm=user_data['npm'], password=user_data['password'])
#             login_user(user)
#             return redirect(url_for('dashboard'))
#         flash('Login Unsuccessful. Check npm and password', 'danger')
#     return render_template('login.html', form=form)

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     return f'Hello, {current_user.nama}! Welcome to your dashboard.'

# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('login'))

# if __name__ == '__main__':
#     app.run(debug=True)
