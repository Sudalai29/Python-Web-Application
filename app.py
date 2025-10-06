######## WITHOUT RDS #########

import os
import logging
import sqlite3
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")
csrf = CSRFProtect(app)

# --- SQLite Setup ---
DB_PATH = os.environ.get("DB_PATH", "app.db")

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # return dict-like rows
    return conn

def init_db():
    """Create table if not exists"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('''
       CREATE TABLE IF NOT EXISTS user_details (
            name TEXT PRIMARY KEY,
            quote TEXT NOT NULL,
            advice TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    logging.info("SQLite DB initialized.")

# Initialize DB
init_db()

# --- Forms ---
class UserForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired(), Length(max=255)])
    quote = TextAreaField("Quote", validators=[DataRequired(), Length(max=500)])
    advice = TextAreaField("Advice", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Submit")

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def input():
    form = UserForm()
    if form.validate_on_submit():
        name = form.username.data.strip()
        quote = form.quote.data.strip()
        advice = form.advice.data.strip()
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO user_details (name, quote, advice, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name)
                DO UPDATE SET quote=excluded.quote, advice=excluded.advice, created_at=CURRENT_TIMESTAMP
            """, (name, quote, advice))
            conn.commit()
            cur.close()
            conn.close()
            flash("✅ Data saved successfully!", "success")
        except Exception as e:
            logging.error(f"Error saving user: {e}")
            flash("⚠️ Failed to save data. Try again.", "danger")
        return redirect(url_for('output'))
    return render_template('index.html', form=form)

@app.route('/output', methods=['GET'])
def output():
    search_name = request.args.get('search', '').strip()
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        if search_name:
            cur.execute("""
                SELECT name, quote, advice, created_at
                FROM user_details
                WHERE name LIKE ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (f"%{search_name}%",))
        else:
            cur.execute("""
                SELECT name, quote, advice, created_at
                FROM user_details
                ORDER BY created_at DESC
                LIMIT 50
            """)
        users = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()

        # Format timestamps
        for user in users:
            if user['created_at']:
                user['created_at'] = datetime.strptime(user['created_at'], "%Y-%m-%d %H:%M:%S").strftime('%d %b %Y %H:%M:%S')
        
        form = UserForm()
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        users = []
        form = UserForm()
        flash("⚠️ Could not fetch data.", "danger")
    return render_template('response.html', users=users, form=form, search=search_name)

@app.route('/delete/<string:name>', methods=['POST'])
def delete_user(name):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM user_details WHERE name = ?", (name,))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"✅ User '{name}' deleted successfully!", "success")
    except Exception as e:
        logging.error(f"Error deleting user {name}: {e}")
        flash("⚠️ Could not delete user.", "danger")
    return redirect(url_for('output'))

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)









######### WITH RDS ###########


# import os
# import json
# import boto3
# import logging
# from datetime import datetime
# from flask import Flask, redirect, url_for, render_template, request, flash
# from flask_wtf import FlaskForm, CSRFProtect
# from wtforms import StringField, TextAreaField, SubmitField
# from wtforms.validators import DataRequired, Length
# import psycopg2
# from psycopg2.extras import RealDictCursor
# from psycopg2 import pool

# # --- Logging ---
# logging.basicConfig(level=logging.INFO)

# # --- Flask Setup ---
# app = Flask(__name__)
# app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")
# csrf = CSRFProtect(app)

# # --- DB Config (from env variables) ---
# ENV = os.environ.get("ENVIRONMENT", "dev")
# REGION_NAME = os.environ.get("REGION_NAME", "ap-south-1")

# SECRET_MAP = {
#     "dev": "myapp-dev-db-secret",
#     "prod": "myapp-prod-db-secret"
# }

# SECRET_NAME = SECRET_MAP.get(ENV, "myapp-dev-db-secret")

# # --- Secrets Manager Integration ---
# _db_secret_cache = None
# _db_pool = None

# def get_db_secret():
#     global _db_secret_cache
#     if _db_secret_cache is None:
#         try:
#             client = boto3.client("secretsmanager", region_name=REGION_NAME)
#             response = client.get_secret_value(SecretId=SECRET_NAME)
#             _db_secret_cache = json.loads(response['SecretString'])
#             logging.info(f"Fetched DB secret for environment '{ENV}'.")
#         except Exception as e:
#             logging.error(f"Failed to retrieve secret '{SECRET_NAME}': {e}")
#             raise
#     return _db_secret_cache

# def init_db_pool(minconn=1, maxconn=5):
#     global _db_pool
#     secret = get_db_secret()
#     _db_pool = pool.SimpleConnectionPool(
#         minconn, maxconn,
#         database=secret["dbname"],
#         user=secret["username"],
#         password=secret["password"],
#         host=secret["host"],
#         port=secret["port"]
#     )
#     logging.info(f"DB connection pool initialized for environment '{ENV}'.")

# def get_db_conn():
#     return _db_pool.getconn()

# def release_db_conn(conn):
#     _db_pool.putconn(conn)

# # --- Database Initialization ---
# def init_db():
#     """Initialize table with timestamp"""
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute('''
#        CREATE TABLE IF NOT EXISTS user_details (
#             name VARCHAR(255) PRIMARY KEY,
#             quote TEXT NOT NULL,
#             advice TEXT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
#     conn.commit()
#     cur.close()
#     release_db_conn(conn)
#     logging.info("DB initialized.")

# # Initialize DB and pool on startup
# init_db_pool()
# init_db()

# # --- Forms ---
# class UserForm(FlaskForm):
#     username = StringField("Name", validators=[DataRequired(), Length(max=255)])
#     quote = TextAreaField("Quote", validators=[DataRequired(), Length(max=500)])
#     advice = TextAreaField("Advice", validators=[DataRequired(), Length(max=500)])
#     submit = SubmitField("Submit")

# # --- Routes ---
# @app.route('/', methods=['GET', 'POST'])
# def input():
#     form = UserForm()
#     if form.validate_on_submit():
#         name = form.username.data.strip()
#         quote = form.quote.data.strip()
#         advice = form.advice.data.strip()
#         try:
#             conn = get_db_conn()
#             cur = conn.cursor()
#             cur.execute("""
#                 INSERT INTO user_details (name, quote, advice)
#                 VALUES (%s, %s, %s)
#                 ON CONFLICT (name)
#                 DO UPDATE SET quote = EXCLUDED.quote, advice = EXCLUDED.advice, created_at = CURRENT_TIMESTAMP
#             """, (name, quote, advice))
#             conn.commit()
#             cur.close()
#             release_db_conn(conn)
#             flash("✅ Data saved successfully!", "success")
#         except Exception as e:
#             logging.error(f"Error saving user: {e}")
#             flash("⚠️ Failed to save data. Try again.", "danger")
#         return redirect(url_for('output'))
#     return render_template('index.html', form=form)

# @app.route('/output', methods=['GET'])
# def output():
#     search_name = request.args.get('search', '').strip()
#     try:
#         conn = get_db_conn()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         if search_name:
#             cur.execute("""
#                 SELECT name, quote, advice, created_at
#                 FROM user_details
#                 WHERE name ILIKE %s
#                 ORDER BY created_at DESC
#                 LIMIT 50
#             """, (f"%{search_name}%",))
#         else:
#             cur.execute("""
#                 SELECT name, quote, advice, created_at
#                 FROM user_details
#                 ORDER BY created_at DESC
#                 LIMIT 50
#             """)
#         users = cur.fetchall()
#         cur.close()
#         release_db_conn(conn)

#         # Format timestamps for readability
#         for user in users:
#             user['created_at'] = user['created_at'].strftime('%d %b %Y %H:%M:%S')
        
#         form = UserForm()
#     except Exception as e:
#         logging.error(f"Error fetching users: {e}")
#         users = []
#         form = UserForm()
#         flash("⚠️ Could not fetch data.", "danger")
#     return render_template('response.html', users=users, form=form, search=search_name)

# @app.route('/delete/<string:name>', methods=['POST'])
# def delete_user(name):
#     try:
#         conn = get_db_conn()
#         cur = conn.cursor()
#         cur.execute("DELETE FROM user_details WHERE name=%s", (name,))
#         conn.commit()
#         cur.close()
#         release_db_conn(conn)
#         flash(f"✅ User '{name}' deleted successfully!", "success")
#     except Exception as e:
#         logging.error(f"Error deleting user {name}: {e}")
#         flash("⚠️ Could not delete user.", "danger")
#     return redirect(url_for('output'))

# # --- Health Check Endpoint ---
# @app.route('/health', methods=['GET'])
# def health():
#     return "OK", 200

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)
