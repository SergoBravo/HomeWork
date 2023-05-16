from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'Aezakmi'  


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL, email TEXT)')
    conn.execute('''CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user)


@app.route('/profile')
def profile():
    if 'username' in session:
        user_id = int(session['user_id'])
        user = get_user_by_id(user_id)
        conn = get_db_connection()
        articles = conn.execute('SELECT * FROM articles WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
        conn.close()
        return render_template('profile.html', user=user, articles=articles)
    else:
        flash('Авторизуйтесь, чтобы просмотреть профиль')
        return redirect(url_for('login'))



def update_profile(user_id, username, email):
    conn = get_db_connection()
    conn.execute('UPDATE users SET username = ?, email = ? WHERE id = ?', (username, email, user_id))
    conn.commit()
    conn.close()


@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        conn = get_db_connection()
        articles = conn.execute('SELECT articles.*, users.username AS author FROM articles JOIN users ON articles.user_id = users.id ORDER BY articles.id DESC').fetchall()
        conn.close()
        return render_template('index.html', username=username, articles=articles)
    else:
        return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))
        existing_user = get_user_by_username(username)
        if existing_user:
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        flash('Регистрация успешна')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['user_id'] = user['id']
            flash('Вход успешен')
            return redirect(url_for('profile'))
        else:
            flash('Неверные имя пользователя или пароль')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' in session:
        if request.method == 'POST':
            user_id = session['user_id']
            username = request.form['username']
            email = request.form['email']
            update_profile(user_id, username, email)
            flash('Профиль успешно обновлен')
            return redirect(url_for('profile'))
        user_id = session['user_id']
        user = get_user_by_id(user_id)
        return render_template('edit_profile.html', user=user)
    else:
        flash('Авторизуйтесь, чтобы редактировать профиль')
        return redirect(url_for('login'))


@app.route('/add_article', methods=['GET', 'POST'])
def add_article():
    if 'username' in session:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            user_id = session['user_id']
            conn = get_db_connection()
            conn.execute('INSERT INTO articles (title, content, user_id) VALUES (?, ?, ?)', (title, content, user_id))
            conn.commit()
            conn.close()
            flash('Статья успешно добавлена')
            return redirect(url_for('index'))
        return render_template('add_article.html')
    else:
        flash('Авторизуйтесь, чтобы добавить статью')
        return redirect(url_for('login'))


@app.route('/edit_article/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    if 'username' in session:
        if request.method == 'POST':
            conn = get_db_connection()
            conn.execute('DELETE FROM articles WHERE id = ?', (article_id,))
            conn.commit()
            conn.close()
            flash('Статья успешно удалена')
            return redirect(url_for('profile'))
        conn = get_db_connection()
        article = conn.execute('SELECT * FROM articles WHERE id = ?', (article_id,)).fetchone()
        conn.close()
        if article:
            return render_template('edit_article.html', article=article)
        else:
            flash('Статья не найдена')
            return redirect(url_for('index'))
    else:
        flash('Авторизуйтесь, чтобы редактировать статью')
        return redirect(url_for('login'))


@app.route('/delete_article/<int:article_id>', methods=['POST'])
def delete_article(article_id):
    if 'username' in session:
        conn = get_db_connection()
        conn.execute('DELETE FROM articles WHERE id = ?', (article_id,))
        conn.commit()
        conn.close()
        flash('Статья успешно удалена')
        return redirect(url_for('profile'))
    else:
        flash('Авторизуйтесь, чтобы удалить статью')
        return redirect(url_for('login'))


create_table()


if __name__ == '__main__':
    create_table()
    app.run(debug=True)

       
