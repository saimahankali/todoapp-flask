# from flask import Flask, render_template, redirect, request, session, url_for
# import mysql.connector as mysql
# from werkzeug.security import generate_password_hash, check_password_hash

# db = mysql.connect(
#     host='localhost',
#     user='root',
#     password='oXVePzWdocvc1LJFlKaGWPWf5VyWJ4UQ',
#     database='sample_j5sf'
# )

from flask import Flask, render_template, redirect, request, session, url_for
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change to a secure key

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host='dpg-cri9jdm8ii6s73d8chg0-a.oregon-postgres.render.com',
        user='root',
        password='oXVePzWdocvc1LJFlKaGWPWf5VyWJ4UQ',
        database='sample_j5sf'
    )
    return conn

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT username FROM "user" WHERE username = %s', (username,))
                record = cur.fetchall()
                if record:
                    return render_template('register.html', msg1='', msg='User Already exists!')
                else:
                    hashed_password = generate_password_hash(password, method='sha256')
                    cur.execute('INSERT INTO "user" (username, password) VALUES (%s, %s)', (username, hashed_password))
                    conn.commit()
                    return render_template('login.html', msg1='SignUp Successful, please Login!')
    return render_template('register.html', msg=' ', msg1='')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM "user" WHERE username = %s', (username,))
                user = cur.fetchone()
                if user and check_password_hash(user[2], password):
                    session['user_id'] = user[0]
                    return redirect('/')
                else:
                    return render_template('login.html', msg='Invalid Credentials')
    return render_template('login.html', msg='')

# User logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

# Home route
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')

    limit = request.args.get('limit', '10')
    limit = int(limit) if limit.isdigit() else 10
    page = int(request.args.get('page', '1'))
    offset = (page - 1) * limit

    search = request.args.get('search', '')
    db = get_db_connection()
    cur = db.cursor()

    try:
        if search:
            search_pattern = f'%{search}%'
            cur.execute("""
                SELECT * FROM taskapp
                WHERE (assignedto ILIKE %s OR status ILIKE %s OR deadline ILIKE %s OR priority ILIKE %s OR info ILIKE %s)
                AND user_id = %s
                LIMIT %s OFFSET %s
            """, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, session['user_id'], limit, offset))
            records = cur.fetchall()

            cur.execute("""
                SELECT count(*) FROM taskapp
                WHERE (assignedto ILIKE %s OR status ILIKE %s OR deadline ILIKE %s OR priority ILIKE %s OR info ILIKE %s)
                AND user_id = %s
            """, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, session['user_id']))
            total_records = cur.fetchone()[0]
        else:
            cur.execute("""
                SELECT * FROM taskapp
                WHERE user_id = %s
                LIMIT %s OFFSET %s
            """, (session['user_id'], limit, offset))
            records = cur.fetchall()

            cur.execute("""
                SELECT count(*) FROM taskapp
                WHERE user_id = %s
            """, (session['user_id'],))
            total_records = cur.fetchone()[0]

        total_pages = (total_records + limit - 1) // limit
    finally:
        cur.close()
        db.close()

    return render_template('index.html', tasks=records, page=page, total_records=total_records, total_pages=total_pages)


# Add task route
@app.route('/addTask')
def addTask():
    return render_template('addTask.html')

# Add task data
@app.route('/addTaskData', methods=['POST'])
def addTaskData():
    if 'user_id' not in session:
        return redirect('/login')

    assigned = request.form['assignedto']
    status = request.form['status']
    deadline = request.form['deadline']
    priority = request.form['priority']
    info = request.form['info']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO taskapp (assignedto, status, deadline, priority, info, user_id) VALUES (%s, %s, %s, %s, %s, %s)',
                        (assigned, status, deadline, priority, info, session['user_id']))
            conn.commit()

    return redirect('/')

# Edit task route
@app.route('/editTask/<int:id>', methods=['GET'])
def editTask(id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM taskapp WHERE id = %s', (id,))
            record = cur.fetchone()
    return render_template('editTask.html', task=record)

# Edit task data
@app.route('/editTaskData/<int:id>', methods=['POST'])
def editTaskData(id):
    assigned = request.form['assignedto']
    status = request.form['status']
    deadline = request.form['deadline']
    priority = request.form['priority']
    info = request.form['info']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE taskapp SET assignedto = %s, status = %s, deadline = %s, priority = %s, info = %s WHERE id = %s',
                        (assigned, status, deadline, priority, info, id))
            conn.commit()

    return redirect('/')

# Delete task route
@app.route('/deleteTask/<int:id>', methods=['GET'])
def deleteTask(id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM taskapp WHERE id = %s', (id,))
            conn.commit()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

