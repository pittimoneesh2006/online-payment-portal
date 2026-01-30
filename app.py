from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
import random, string

app = Flask(__name__)
app.secret_key = "supersecurekey_2025"

# ===========================
# Database Connection
# ===========================
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # enter your MySQL password if any
            database="payment_portal"
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Database error: {e}")
    return None

# ===========================
# Captcha Generator
# ===========================
def generate_captcha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# ===========================
# Login
# ===========================
@app.route('/', methods=['GET', 'POST'])
def login():
    captcha = generate_captcha()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        captcha_input = request.form['captcha']
        real_captcha = request.form['real_captcha']

        if captcha_input != real_captcha:
            flash("⚠️ Invalid CAPTCHA! Try again.", "danger")
            return redirect(url_for('login'))

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return redirect(url_for('login'))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['loggedin'] = True
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("❌ Invalid username or password.", "danger")

    return render_template('login.html', captcha=captcha)

# ===========================
# Signup
# ===========================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, password))
        conn.commit()
        cursor.close()
        conn.close()

        flash("🎉 Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# ===========================
# Dashboard
# ===========================
@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ua.main_balance, ua.savings_balance, ua.reward_points
        FROM user_accounts ua
        JOIN users u ON u.user_id = ua.user_id
        WHERE u.username = %s
    """, (session['username'],))
    account = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('dashboard.html', username=session['username'], account=account)

# ===========================
# Logout
# ===========================
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)