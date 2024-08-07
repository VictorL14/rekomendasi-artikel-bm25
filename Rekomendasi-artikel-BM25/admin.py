from flask import Flask, render_template, request, redirect, url_for, session
from flaskext.mysql import MySQL

app = Flask(__name__)
mysql = MySQL()

# Konfigurasi MySQL
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'rekomendasi_artikel'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

# Fungsi untuk membuat koneksi ke database
def get_db_connection():
    return mysql.connect()

# Fungsi untuk melakukan login admin
def login_admin(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM admin WHERE username = %s AND password = %s', (username, password))
    admin = cursor.fetchone()

    cursor.close()
    conn.close()

    return admin

# Fungsi untuk menampilkan halaman login admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = login_admin(username, password)

        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password.')

    return render_template('login.html')

# Fungsi untuk logout admin
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Fungsi untuk menampilkan dashboard admin
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    return render_template('dashboard.html')

# Fungsi untuk menambahkan artikel baru
@app.route('/admin/article/add', methods=['GET', 'POST'])
def add_article():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        # Ambil data dari form
        title = request.form['title']
        content = request.form['content']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query untuk menambahkan artikel baru ke dalam database
        cursor.execute('INSERT INTO articles (title, content) VALUES (%s, %s)', (title, content))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('admin_dashboard'))

    return render_template('add_article.html')

# Fungsi untuk menampilkan daftar artikel
@app.route('/admin/article/list')
def list_articles():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Query untuk mendapatkan daftar artikel dari database
    cursor.execute('SELECT * FROM articles')
    articles = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('list_articles.html', articles=articles)

# Fungsi untuk mengedit artikel
@app.route('/admin/article/edit/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Ambil data dari form
        title = request.form['title']
        content = request.form['content']

        # Query untuk mengupdate artikel
        cursor.execute('UPDATE articles SET title = %s, content = %s WHERE id = %s', (title, content, id))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('list_articles'))

    # Ambil data artikel yang akan di-edit
    cursor.execute('SELECT * FROM articles WHERE id = %s', (id,))
    article = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('edit_article.html', article=article)

# Fungsi untuk menghapus artikel
@app.route('/admin/article/delete/<int:id>', methods=['POST'])
def delete_article(id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Query untuk menghapus artikel
    cursor.execute('DELETE FROM articles WHERE id = %s', (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('list_articles'))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(debug=True)
