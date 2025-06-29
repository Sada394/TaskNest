from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'fgh123789@&&'

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sada123456@$",
    database="tasknest_db"
)
cursor = conn.cursor(dictionary=True)

# ------------------ LOGIN ------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email_prefix'] + "@gmail.com"

        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid Email or Password", show_forgot=True)

    return render_template('login.html', show_forgot=False)

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email_prefix'] + "@gmail.com"

        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error="Passwords match nahi kartay")

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return render_template('register.html', error="Email already exists")

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hashed_password))
        conn.commit()

        # Auto login after registration
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect('/dashboard')
    return render_template('register.html')

# ------------------ FORGOT PASSWORD ------------------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email_prefix'] + "@gmail.com"

        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            session['reset_email'] = email
            return redirect('/reset-password')
        else:
            return render_template('forgot_password.html', error="Yeh email registered nahi hai.")
    return render_template('forgot_password.html')

# ------------------ RESET PASSWORD ------------------
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    if not email:
        return redirect('/')

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('reset_password.html', error="Passwords match nahi kar rahe.")

        hashed = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed, email))
        conn.commit()
        session.pop('reset_email', None)
        return redirect('/')
    return render_template('reset_password.html')

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (session['user_id'],))
    tasks = cursor.fetchall()
    return render_template('dashboard.html', username=session['username'], tasks=tasks)

# ------------------ EDIT TASK ------------------
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect('/')
    
    # Fetch current task
    cursor.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    task = cursor.fetchone()

    if not task:
        return "Task not found", 404

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description') or ""
        due_date = request.form.get('due_date') or None
        priority = request.form.get('priority') or "Medium"

        cursor.execute("""
            UPDATE tasks
            SET title=%s, description=%s, due_date=%s, priority=%s
            WHERE id=%s AND user_id=%s
        """, (title, description, due_date, priority, task_id, session['user_id']))
        conn.commit()

        return redirect('/dashboard')

    return render_template('edit_task.html', task=task)


# ------------------ ADD TASK ------------------
@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/')
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description') or ""
        due_date = request.form.get('due_date') or None
        priority = request.form.get('priority') or "Medium"

        cursor.execute("""
            INSERT INTO tasks (user_id, title, description, due_date, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['user_id'], title, description, due_date, priority, 'pending'))
        conn.commit()

        return redirect('/dashboard')

    return render_template('add_task.html')

# ------------------ COMPLETE TASK ------------------
@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect('/')
    
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    conn.commit()
    return redirect('/dashboard')

# ------------------ DELETE TASK ------------------
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect('/')
    
    cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    conn.commit()
    return redirect('/dashboard')


if __name__ == '__main__':
    app.run(debug=True)
