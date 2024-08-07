from routes import main
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from werkzeug.utils import safe_join, secure_filename
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import DataRequired
from flask_paginate import Pagination, get_page_parameter
from models import *
import pandas as pd
from datetime import datetime
import MySQLdb
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from MySQLdb.cursors import DictCursor
from flask import render_template, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'victor14'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_DB'] = 'rekomendasi_bm25'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = r'C:\Users\victo\Documents\python_final\folder_upload'

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class LoginForm(FlaskForm):
    npm = StringField('NPM', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class LoginFormAdmin(FlaskForm):
    nama_admin = StringField('Nama Admin', validators=[DataRequired()])
    password_admin = PasswordField('Password Admin', validators=[DataRequired()])
    submit_admin = SubmitField('Login')

class SignupForm(FlaskForm):
    nama = StringField('Nama', validators=[DataRequired()])
    npm = StringField('NPM', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Signup')

class SignupFormAdmin(FlaskForm):
    nama_admin = StringField('Nama Admin', [DataRequired()])
    password_admin = PasswordField('Password Admin', [DataRequired()])
    submit_admin = SubmitField('Signup')

class Pengguna(UserMixin):
    def __init__(self, id, nama, npm, password, session_ke):
        self.id = id
        self.nama = nama
        self.npm = npm
        self.password = password
        self.session_ke = session_ke
        self.likes = set()  # Menyimpan ID artikel yang di-like

    def get_id(self):
        return f'user:{self.id}'
    
    def like_article(self, article_id):
        self.likes.add(article_id)

    def unlike_article(self, article_id):
        self.likes.discard(article_id)

    def has_liked(self, article_id):
        return article_id in self.likes

class Admin(UserMixin):
    def __init__(self, id, nama_admin, password_admin):
        self.id = id
        self.nama_admin = nama_admin
        self.password_admin = password_admin

    def get_id(self):
        return f'admin:{self.id}'

@login_manager.user_loader
def load_user(user_id):
    try:
        user_type, id = user_id.split(':')
    except ValueError:
        return None

    cur = mysql.connection.cursor()

    if user_type == 'user':
        cur.execute("SELECT * FROM pengguna WHERE id = %s", (id,))
        user_data = cur.fetchone()
        cur.close()
        if user_data:
            return Pengguna(id=user_data['id'], nama=user_data['nama'], npm=user_data['npm'], password=user_data['password'], session_ke=user_data['session_ke'])
    elif user_type == 'admin':
        cur.execute("SELECT * FROM admin WHERE id = %s", (id,))
        admin_data = cur.fetchone()
        cur.close()
        if admin_data:
            return Admin(id=admin_data['id'], nama_admin=admin_data['nama_admin'], password_admin=admin_data['password_admin'])
    return None




@app.route('/')
def landingpage():
    return render_template('landing_page.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO pengguna (nama, npm, password) VALUES (%s, %s, %s)",
                    (form.nama.data, form.npm.data, hashed_password))
        mysql.connection.commit()
        cur.close()
        print(f"Pengguna {form.nama.data} berhasil mendaftar.")
        flash('Signup Successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    else:
        print("Form validation failed")
    return render_template('signup.html', form=form)


@app.route('/signupadmin', methods=['GET', 'POST'])
def signupadmin():
    form_admin = SignupFormAdmin()
    if form_admin.validate_on_submit():
        hashed_password = generate_password_hash(form_admin.password_admin.data, method='sha256')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO admin (nama_admin, password_admin) VALUES (%s, %s)", (form_admin.nama_admin.data, hashed_password))
        mysql.connection.commit()
        cur.close()
        flash('Signed up successfully!', 'success')
        return redirect(url_for('login_admin'))
    return render_template('signup_admin.html', form_admin=form_admin)

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    form_admin = LoginFormAdmin()
    if form_admin.validate_on_submit():
        nama_admin = form_admin.nama_admin.data
        password_admin = form_admin.password_admin.data

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE nama_admin = %s", (nama_admin,))
        admin_data = cur.fetchone()
        cur.close()

        if admin_data and check_password_hash(admin_data['password_admin'], password_admin):
            admin = Admin(id=admin_data['id'], nama_admin=admin_data['nama_admin'], password_admin=admin_data['password_admin'])
            login_user(admin)
            session['user_type'] = 'admin'
            flash('Admin berhasil login.', 'success')
            return redirect(url_for('dashboard_admin'))
        else:
            flash('Nama admin atau password salah.', 'danger')

    return render_template('login_admin.html', form_admin=form_admin)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM pengguna WHERE npm = %s", (form.npm.data,))
        user_data = cur.fetchone()
        if user_data:
            if check_password_hash(user_data['password'], form.password.data):
                # Increment session_ke
                new_session_ke = user_data['session_ke'] + 1
                cur.execute("UPDATE pengguna SET session_ke = %s WHERE id = %s", (new_session_ke, user_data['id']))
                mysql.connection.commit()
                
                
                # Create user object with updated session_ke
                user = Pengguna(id=user_data['id'], nama=user_data['nama'], npm=user_data['npm'], password=user_data['password'], session_ke=new_session_ke)
                login_user(user)
                session['user_type'] = 'user'
                print(f"Pengguna {form.npm.data} berhasil login dengan session_ke {new_session_ke}.")
                return redirect(url_for('homepage'))
            else:
                cur.close()
                print(f"Password salah untuk pengguna {form.npm.data}.")
                flash('Login Unsuccessful. Check NPM and password', 'danger')
        else:
            cur.close()
            print(f"Pengguna dengan NPM {form.npm.data} tidak ditemukan.")
            flash('Login Unsuccessful. Check NPM and password', 'danger')
    else:
        print("Form validation failed")
    return render_template('login.html', form=form)





@app.route('/homepage')
@login_required
def homepage():
    if not isinstance(current_user, Pengguna):
        return redirect(url_for('login'))
    
    user_id = current_user.id
    cur = mysql.connection.cursor()
    cur.execute('SELECT kueri FROM kueri WHERE pengguna_id = %s', (user_id,))
    queries = cur.fetchall()

    # Combine all unique queries into a single string
    unique_queries = set(query['kueri'] for query in queries)
    combined_query = ' '.join(unique_queries)
    
    # Preprocess the combined query if it's not empty
    preprocessed_query = preprocess_query(combined_query)

    # Fetch all articles from the database
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM artikel')
    articles = cur.fetchall()
    
    # Fetch setup values
    # Mengambil semua nilai setup
    cur.execute('SELECT nama_setup, nilai_setup FROM setup')
    setup_values = cur.fetchall()

    # Menginisialisasi variabel
    k1 = None
    b = None
    n = None

    # Menampilkan nilai yang diambil
    print("Nilai setup yang diambil:", setup_values)

    # Mengisi nilai ke dalam variabel k1, b, dan n
    for item in setup_values:
        if item['nama_setup'] == 'k1':
            k1 = item['nilai_setup']
        elif item['nama_setup'] == 'b':
            b = item['nilai_setup']
        elif item['nama_setup'] == 'n':
            n = int(item['nilai_setup'])

    cur.close()
    # Convert articles to DataFrame
    columns = ['id', 'judul_awal', 'judul', 'abstrak', 'tahun', 'nama_penulis', 'file_path']
    af = pd.DataFrame(articles, columns=columns)
    


    # Calculate BM25 scores for titles
    skor_bm25_judul = calculate_bm25_judul(preprocessed_query, af, k1, b)
    bm25_scores_judul = []
    for index, row in af.iterrows():
        bm25_score = skor_bm25_judul.get(index, 0)  # Default to 0 if index not found
        bm25_scores_judul.append(bm25_score)
    af['bm25_score_judul'] = bm25_scores_judul
    
    # Calculate BM25 scores for abstracts
    skor_bm25_abstrak = calculate_bm25_abstrak(preprocessed_query, af, k1, b)
    bm25_scores_abstrak = []
    for index, row in af.iterrows():
        bm25_score = skor_bm25_abstrak.get(index, 0)  # Default to 0 if index not found
        bm25_scores_abstrak.append(bm25_score)
    af['bm25_score_abstrak'] = bm25_scores_abstrak
    
    # Calculate BM25 scores for combined titles and abstracts
    skor_bm25_judul_abstrak = calculate_bm25_judul_abstrak(preprocessed_query, af, k1, b)
    bm25_scores_gabungan = []
    for index, row in af.iterrows():
        bm25_score = skor_bm25_judul_abstrak.get(index, 0)  # Default to 0 if index not found
        bm25_scores_gabungan.append(bm25_score)
    af['bm25_score_gabungan'] = bm25_scores_gabungan
    
    af['download_url'] = af['id'].apply(lambda x: url_for('download_file', id=x))
    af['tahun'] = pd.to_datetime(af['tahun'], format='%Y')
    af['tahun_format'] = af['tahun'].dt.strftime('%Y')
    # Ambil 5 teratas berdasarkan skor BM25
    judul_top5 = af[['id', 'judul_awal', 'nama_penulis', 'tahun_format', 'bm25_score_judul', 'download_url']].sort_values(by='bm25_score_judul', ascending=False).head(n).to_dict(orient='records')
    abstrak_top5 = af[['id', 'judul_awal', 'nama_penulis', 'tahun_format', 'bm25_score_abstrak', 'download_url']].sort_values(by='bm25_score_abstrak', ascending=False).head(n).to_dict(orient='records')
    gabungan_top5 = af[['id', 'judul_awal', 'nama_penulis', 'tahun_format', 'bm25_score_gabungan', 'download_url']].sort_values(by='bm25_score_gabungan', ascending=False).head(n).to_dict(orient='records')
   
    return render_template(
        'homepage.html',
        judul=judul_top5,
        abstrak=abstrak_top5,
        gabungan=gabungan_top5
    )
    
@app.route('/toggle_like', methods=['POST'])
@login_required
def toggle_like():
    if not isinstance(current_user, Pengguna):
        return redirect(url_for('login'))
    
    data = request.get_json()
    article_id = data['article_id']
    is_liked = data['is_liked']
    category = data['category']
    user_id = current_user.id

    if session.get('user_type') == 'admin':
        return jsonify({'success': False, 'error': 'Admins cannot like articles'})

    try:
        conn = mysql.connection
        cursor = conn.cursor()
        
        # Retrieve setup values
        cursor.execute('SELECT nama_setup, nilai_setup FROM setup')
        setup_values = cursor.fetchall()

        cursor.execute('SELECT session_ke FROM pengguna WHERE id = %s', (user_id,))
        results = cursor.fetchall()
        for row in results:
            session_ke = row['session_ke']  # Jika menggunakan cursor DictCursor
            # Lakukan sesuatu dengan session_ke


        # Initialize variables
        k1 = None
        b = None
        n = None

        # Assign values to k1, b, and n from setup_values
        for item in setup_values:
            if item['nama_setup'] == 'k1':
                k1 = item['nilai_setup']
            elif item['nama_setup'] == 'b':
                b = item['nilai_setup']
            elif item['nama_setup'] == 'n':
                n = int(item['nilai_setup'])

        if is_liked:
            cursor.execute('DELETE FROM likes WHERE pengguna_id = %s AND artikel_id = %s AND kategori = %s', (user_id, article_id, category))
            action = 'unliked'
        else:
            cursor.execute('INSERT INTO likes (pengguna_id, artikel_id, kategori, k1, b, n, session) VALUES (%s, %s, %s, %s, %s, %s, %s)', (user_id, article_id, category, k1, b, n, session_ke))
            action = 'liked'

        conn.commit()
        return jsonify({'success': True, 'action': action})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()




@app.route('/download/<int:id>', methods=['GET'])
def download_file(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT file_path FROM artikel WHERE id = %s", (id,))
        result = cur.fetchone()
        cur.close()

        if result is None:
            flash('File not found in database', 'error')
            return redirect(url_for('search_articles'))

        file_path = result['file_path']  # Akses menggunakan nama kolom
        return send_file(file_path, as_attachment=True)

    except MySQLdb.Error as e:
        flash(f"Error accessing database: {str(e)}", 'error')
        return redirect(url_for('search_articles'))
    
    
    
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_articles():
    if not isinstance(current_user, Pengguna):
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    query = request.form.get('query') if request.method == 'POST' else request.args.get('query', '')

    if request.method == 'POST':
        if not query:
            flash('Query is required', 'danger')
            return redirect(url_for('search_articles'))

        # Preprocess query: split into individual words
        preprocessed_query = preprocess_query(query)
        search_words = preprocessed_query.split()

        # Build the SQL query with LIKE for each word in the search query
        search_conditions = " OR ".join(
            ["judul LIKE %s" for _ in search_words] + 
            ["abstrak LIKE %s" for _ in search_words]
        )
        search_params = ["%" + word + "%" for word in search_words] * 2

        sql_query = f"SELECT * FROM artikel WHERE {search_conditions}"

        cur = mysql.connection.cursor(DictCursor)
        cur.execute(sql_query, search_params)
        articles = cur.fetchall()
        cur.close()

        # If no articles are found
        if not articles:
            flash('No articles found', 'warning')
            return redirect(url_for('search_articles'))

        # Save query and results to the database
        now = datetime.now()
        user_id = current_user.id

        # Insert query into kueri table
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO kueri (pengguna_id, kueri, waktu) VALUES (%s, %s, %s)', (user_id, query, now))
        kueri_id = cur.lastrowid
        mysql.connection.commit()

        # Insert each result into kueri table with associated artikel_id
        for article in articles:
            artikel_id = article['id']
            cur.execute('INSERT INTO kueri (pengguna_id, artikel_id, kueri, waktu) VALUES (%s, %s, %s, %s)', (user_id, artikel_id, query, now))

        mysql.connection.commit()
        cur.close()

        # Prepare data for rendering
        search_results = [
            {
                'judul_awal': article['judul_awal'],
                'nama_penulis': article['nama_penulis'],
                'abstrak': article['abstrak'],
                'tahun': article['tahun'],
                'download_link': url_for('download_file', id=article['id'])
            }
            for article in articles
        ]

        # Pagination logic
        per_page = 10
        total_pages = (len(search_results) + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = search_results[start:end]

        return render_template(
            'pencarian.html',
            kueri_hasil=query,
            hasil=paginated_results,
            pagination={
                'page': page,
                'total_pages': total_pages
            },
            max=max,
            min=min,
            query=query
        )

    return render_template('homepage.html')



@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not isinstance(current_user, Pengguna):
        return redirect(url_for('login'))
    
    user_id = current_user.id
    cur = mysql.connection.cursor()
    cur.execute("SELECT nama, npm FROM pengguna WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    
    if request.method == 'POST':
        nama = request.form['nama']
        npm = request.form['npm']
        cur.execute("""
            UPDATE pengguna 
            SET nama = %s, npm = %s
            WHERE id = %s
        """, (nama, npm, user_id))
        mysql.connection.commit()
        flash('Profil berhasil diperbarui!', 'success')
        return redirect(url_for('profile'))

    # Get liked articles
    cur.execute("""
    SELECT artikel.id, artikel.judul_awal, likes.kategori
    FROM artikel 
    JOIN likes ON artikel.id = likes.artikel_id 
    WHERE likes.pengguna_id = %s
""", (user_id,))

    liked_articles = cur.fetchall()
    cur.close()

    return render_template('profile.html', user=user_data, liked_articles=liked_articles, enumerate=enumerate)

@app.route('/delete_like', methods=['POST'])
@login_required
def delete_like():
    data = request.get_json()
    article_id = data['article_id']
    user_id = current_user.id

    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute('DELETE FROM likes WHERE pengguna_id = %s AND artikel_id = %s', (user_id, article_id))
        conn.commit()

        current_user.unlike_article(article_id)

        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()



@app.route('/admin_setup', methods=['POST'])
@login_required
def admin_setup():
    k1 = request.form['k1']
    b = request.form['b']
    n = request.form['n']

    cur = mysql.connection.cursor()
    cur.execute('UPDATE setup SET nilai_setup = %s WHERE nama_setup = %s', (k1, 'k1'))
    cur.execute('UPDATE setup SET nilai_setup = %s WHERE nama_setup = %s', (b, 'b'))
    cur.execute('UPDATE setup SET nilai_setup = %s WHERE nama_setup = %s', (n, 'n'))
    mysql.connection.commit()
    cur.close()

    flash('Setup values updated successfully!', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/dashboard_admin')
@login_required
def dashboard_admin():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin

    cur = mysql.connection.cursor()

    # Hitung jumlah pengguna
    cur.execute("SELECT COUNT(*) as jumlah FROM pengguna")
    result = cur.fetchone()
    jumlah_pengguna = result['jumlah'] if result else 0

    # Hitung jumlah artikel
    cur.execute("SELECT COUNT(*) as jumlah FROM artikel")
    result = cur.fetchone()
    jumlah_artikel = result['jumlah'] if result else 0
    
    # Fetch setup values
    cur.execute('SELECT nama_setup, nilai_setup FROM setup')
    setup_values = cur.fetchall()
    setup_dict = {item['nama_setup']: item['nilai_setup'] for item in setup_values}

    setup = {
        'k1': setup_dict.get('k1', 1.5),
        'b': setup_dict.get('b', 0.75),
        'n': setup_dict.get('n', 10)
    }

    cur.close()

    return render_template('dashboard_admin.html', admin_name=admin_name, jumlah_pengguna=jumlah_pengguna, jumlah_artikel=jumlah_artikel, setup=setup)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    user_type = session.pop('user_type', None)
    logout_user()
    
    if user_type == 'admin':
        return redirect(url_for('login_admin'))
    else:
        return redirect(url_for('login'))

@app.route('/dashboard_artikel')
@login_required
def dashboard_artikel():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin
    search_query = request.args.get('search', default="", type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    cur = mysql.connection.cursor()

    if search_query:
        query = "SELECT * FROM artikel WHERE judul_awal LIKE %s LIMIT %s OFFSET %s"
        cur.execute(query, ("%" + search_query + "%", per_page, (page - 1) * per_page))
    else:
        cur.execute("SELECT * FROM artikel LIMIT %s OFFSET %s", (per_page, (page - 1) * per_page))
    
    melihat_artikel = cur.fetchall()

    # Get total number of items for pagination
    if search_query:
        query = "SELECT COUNT(*) as jumlah FROM artikel WHERE judul_awal LIKE %s"
        cur.execute(query, ("%" + search_query + "%",))
    else:
        cur.execute("SELECT COUNT(*) as jumlah FROM artikel")
    
    result = cur.fetchone()
    total_items = result['jumlah'] if result else 0
    cur.close()

    pagination = {
        'total_items': total_items,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_items + per_page - 1) // per_page
    }

    return render_template('dashboard_artikel.html', melihat_artikel=melihat_artikel, search_query=search_query, pagination=pagination, max=max,
    min=min)



@app.route('/edit_artikel/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_artikel(id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM artikel WHERE id = %s", (id,))
    artikel = cur.fetchone()
    
    if request.method == 'POST':
        judul_awal = request.form['judul_awal']
        judul = request.form['judul']
        abstrak = request.form['abstrak']
        tahun = request.form['tahun']
        nama_penulis = request.form['nama_penulis']
        
        cur.execute("""
            UPDATE artikel 
            SET judul_awal = %s, judul = %s, abstrak = %s, tahun = %s, nama_penulis = %s 
            WHERE id = %s
        """, (judul_awal, judul, abstrak, tahun, nama_penulis, id))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('dashboard_artikel'))
    
    cur.close()
    return render_template('edit_artikel.html', artikel=artikel)

# Fungsi untuk mengunggah dan memproses PDF
@app.route('/upload_pdf', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Proses PDF
            abstract = extract_abstract(file_path)
            title = extract_title_from_pdf(file_path)
            year = extract_year_from_pdf(file_path)
            authors = extract_authors_from_pdf(file_path)
            raw_title = extract_raw_title_from_pdf(file_path)

            # Simpan ke database
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO artikel (judul_awal, judul, abstrak, tahun, nama_penulis, file_path) VALUES (%s, %s, %s, %s, %s, %s)",
                (raw_title, title, abstract, year, ', '.join(authors), file_path)
            )
            mysql.connection.commit()
            cur.close()

            flash('File successfully uploaded and processed', 'success')
            return redirect(url_for('dashboard_artikel'))

    return render_template('dashboard_artikel.html')

@app.route('/delete_artikel/<int:id>', methods=['POST'])
@login_required
def delete_artikel(id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM artikel WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('dashboard_artikel'))

@app.route('/dashboard_penilaian')
@login_required
def dashboard_penilaian():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    cursor = mysql.connection.cursor()

    try:
        # Mengambil data pengguna yang memiliki likes beserta nilai k1, b, dan n dari likes
        # Mengambil data pengguna yang memiliki likes beserta nilai k1, b, dan n dari likes
        cursor.execute('''
            SELECT p.id, p.nama, p.npm, l.k1, l.b, l.n, l.kategori, COUNT(l.kategori) as like_count
            FROM pengguna p
            JOIN likes l ON p.id = l.pengguna_id
            GROUP BY p.id, p.nama, p.npm, l.k1, l.b, l.n, l.kategori
        ''')
        like_counts = cursor.fetchall()

        # Debug: Print like_counts
        print("Like counts:", like_counts)

        # Menginisialisasi penilaian data
        penilaian_data = []
        session_dict = {}

        for pengguna in like_counts:
            pengguna_id = pengguna['id']
            session_key = (pengguna_id, pengguna['k1'], pengguna['b'], pengguna['n'])

            if session_key not in session_dict:
                session_dict[session_key] = {
                    'penilaian': {
                        'nama': pengguna['nama'],
                        'npm': pengguna['npm'],
                        'k1': pengguna['k1'],
                        'b': pengguna['b'],
                        'n': pengguna['n'],
                        'nilai_judul': 0,
                        'nilai_abstrak': 0,
                        'nilai_gabungan': 0
                    }
                }

            if pengguna['kategori'] == 'judul':
                session_dict[session_key]['penilaian']['nilai_judul'] = min(pengguna['like_count'] / pengguna['n'], 1)
            elif pengguna['kategori'] == 'abstrak':
                session_dict[session_key]['penilaian']['nilai_abstrak'] = min(pengguna['like_count'] / pengguna['n'], 1)
            elif pengguna['kategori'] == 'gabungan':
                session_dict[session_key]['penilaian']['nilai_gabungan'] = min(pengguna['like_count'] / pengguna['n'], 1)

        penilaian_data = list(session_dict.values())

        # Debug: Print penilaian_data
        print("Penilaian data:", penilaian_data)

        return render_template('dashboard_penilaian.html', penilaian_data=penilaian_data)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    finally:
        cursor.close()






@app.route('/dashboard_pengguna')
@login_required
def dashboard_pengguna():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin
    search_query = request.args.get('search', default="", type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    cur = mysql.connection.cursor()

    # Mengambil pengguna sesuai dengan query pencarian dan paginasi
    if search_query:
        query = "SELECT * FROM pengguna WHERE npm LIKE %s LIMIT %s OFFSET %s"
        cur.execute(query, ("%" + search_query + "%", per_page, (page - 1) * per_page))
    else:
        cur.execute("SELECT * FROM pengguna LIMIT %s OFFSET %s", (per_page, (page - 1) * per_page))
    
    melihat_pengguna = cur.fetchall()

    # Mengambil total jumlah pengguna untuk paginasi
    if search_query:
        query = "SELECT COUNT(*) as jumlah FROM pengguna WHERE npm LIKE %s"
        cur.execute(query, ("%" + search_query + "%",))
    else:
        cur.execute("SELECT COUNT(*) as jumlah FROM pengguna")
    
    result = cur.fetchone()
    total_items = result['jumlah'] if result else 0
    cur.close()

    # Menghitung informasi paginasi
    pagination = {
        'total_items': total_items,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_items + per_page - 1) // per_page
    }

    return render_template('dashboard_pengguna.html', melihat_pengguna=melihat_pengguna, search_query=search_query, pagination=pagination, max=max, min=min)


@app.route('/edit_pengguna/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_pengguna(id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pengguna WHERE id = %s", (id,))
    pengguna = cur.fetchone()
    
    if request.method == 'POST':
        nama = request.form['nama']
        npm = request.form['npm']
        
        cur.execute("""
            UPDATE pengguna 
            SET nama = %s, npm = %s
            WHERE id = %s
        """, (nama, npm, id))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('dashboard_pengguna'))
    
    cur.close()
    return render_template('edit_pengguna.html', pengguna=pengguna)

@app.route('/delete_pengguna/<int:id>', methods=['POST'])
@login_required
def delete_pengguna(id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    admin_name = current_user.nama_admin
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM pengguna WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('dashboard_pengguna'))


if __name__ == '__main__':
    app.run(debug=True)
