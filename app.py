# from flask import Flask, render_template, redirect, request, session, url_for
# import mysql.connector as mysql
# from werkzeug.security import generate_password_hash, check_password_hash

# db = mysql.connect(
#     host='localhost',
#     user='root',
#     password='12345678',
#     database='sample'
# )

from flask import Flask, render_template, redirect, request, session, url_for
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Database connection
db = psycopg2.connect(
    host='your_host',
    user='your_user',
    password='your_password',
    dbname='your_database'
)

cur = db.cursor()

app = Flask(__name__)
app.secret_key = 'ms123'

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        sql = 'select username from user where username = %s'
        cur.execute(sql,(username,))
        record = cur.fetchall()
        print(record)
        if len(record) != 0:
            return render_template('register.html',msg1='',msg = 'User Already exists!')
        else:
            hashed_password = generate_password_hash(password, method='sha256')
            cur.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, hashed_password))
            db.commit()
            return render_template('/login.html',msg1 = 'SignUp Sucessfull please Login!')
    return render_template('register.html',msg=' ',msg1 = '')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        sql = 'select username from user where username = %s'
        cur.execute(sql,(username,))
        record = cur.fetchall()
        if len(record) == 0:
            return render_template('login.html',msg = 'User does not exist!')
        cur.execute('SELECT * FROM user WHERE username = %s', (username,))
        user = cur.fetchone()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return render_template('login.html',msg = 'Invalid Credentials')
    return render_template('login.html',msg = '')

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
    if not limit or not limit.isdigit():
        limit = 10
    else:
        limit = int(limit)

    page = int(request.args.get('page', '1'))
    offset = (page - 1) * limit

    search = request.args.get('search', '')

    if search:
        sql = """
            SELECT * FROM taskapp
            WHERE (assignedto LIKE %s OR status LIKE %s OR deadline LIKE %s OR priority LIKE %s OR info LIKE %s)
            AND user_id = %s
            LIMIT %s OFFSET %s
        """
        search_pattern = f'%{search}%'
        values = (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, session['user_id'], limit, offset)
        
        cur.execute(sql, values)
        records = cur.fetchall()

        cur.execute("""
            SELECT count(*) FROM taskapp
            WHERE (assignedto LIKE %s OR status LIKE %s OR deadline LIKE %s OR priority LIKE %s OR info LIKE %s)
            AND user_id = %s
        """, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, session['user_id']))
        total_records = cur.fetchone()[0]
    else:
        sql = """
            SELECT * FROM taskapp
            WHERE user_id = %s
            LIMIT %s OFFSET %s
        """
        values = (session['user_id'], limit, offset)
        
        cur.execute(sql, values)
        records = cur.fetchall()

        cur.execute("""
            SELECT count(*) FROM taskapp
            WHERE user_id = %s
        """, (session['user_id'],))
        total_records = cur.fetchone()[0]

    total_pages = (total_records + limit - 1) // limit

    return render_template('index.html', tasks=records, page=page, total_records=total_records, total_pages=total_pages)


@app.route('/addTask')
def addTask():
    return render_template('addTask.html')


# Add task route
@app.route('/addTaskData', methods=['POST'])
def addTaskData():
    if 'user_id' not in session:
        return redirect('/login')

    assigned = request.form['assignedto']
    status = request.form['status']
    deadline = request.form['deadline']
    priority = request.form['priority']
    info = request.form['info']
    sql = 'INSERT INTO taskapp (assignedto, status, deadline, priority, info, user_id) VALUES (%s, %s, %s, %s, %s, %s)'
    values = (assigned, status, deadline, priority, info, session['user_id'])
    cur.execute(sql, values)
    db.commit()
    return redirect('/')


@app.route('/editTask/<int:id>',methods = ['get'])
def editTask(id):
    sql = 'select * from taskapp where id = %s'
    values = (id,)
    cur.execute(sql,values)
    record = cur.fetchone()
    return render_template('editTask.html',task = record)


@app.route('/editTaskData/<int:id>',methods = ['post'])
def editTaskData(id):
    sql = 'update taskapp set assignedto = %s,status = %s, deadline = %s,priority = %s, info = %s where id = %s'
    assigned = request.form['assignedto']
    status = request.form['status']
    deadline = request.form['deadline']
    priority = request.form['priority']
    info = request.form['info']
    values = (assigned,status,deadline,priority,info,id)
    cur.execute(sql,values)
    db.commit()
    return redirect('/')

@app.route('/deleteTask/<int:id>',methods=['get'])
def deleteTask(id):
    sql = 'delete from taskapp where id = %s'
    values = (id,)
    cur.execute(sql,values)
    db.commit()
    return redirect('/')
# Edit and delete routes remain the same, just add a check to ensure the user is logged in

if __name__ == '__main__':
    app.run(debug=True)
