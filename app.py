# import boto3
# import json
# from flask import Flask, redirect, url_for, render_template, request
# import psycopg2

# DB_NAME="postgres"
# DB_HOST="python-db.cvyas68miksx.ap-south-1.rds.amazonaws.com"
# DB_PORT="5432"

# app = Flask(__name__)

# # Change these values to match your setup
# SECRET_NAME = "rds!db-cfce6876-8455-42f4-8483-ab87766c6393"   # The secret name in Secrets Manager
# REGION_NAME = "ap-south-1"          # AWS region where your secret is stored


# # --- Secrets Manager Integration ---
# _db_secret_cache = None  # simple cache

# def get_db_secret():
#     """Fetch DB credentials from AWS Secrets Manager"""
#     global _db_secret_cache
#     if _db_secret_cache is None:
#         client = boto3.client("secretsmanager", region_name=REGION_NAME)
#         response = client.get_secret_value(SecretId=SECRET_NAME)
#         _db_secret_cache = json.loads(response['SecretString'])
#     return _db_secret_cache


# # --- Database Connection ---
# def connect_db():
#     secret = get_db_secret()
#     conn = psycopg2.connect(
#         database=DB_NAME,
#         user=secret["username"],
#         password=secret["password"],
#         host=DB_HOST,
#         port=DB_PORT
#     )
#     return conn


# def create_cursor():
#     conn = connect_db()
#     cur = conn.cursor()
#     return conn, cur


# def close_db(conn, cur):
#     cur.close()
#     conn.close()


# # --- Initialize Table ---
# def init_db():
#     conn, cur = create_cursor()
#     cur.execute('''
#        CREATE TABLE IF NOT EXISTS user_details (
#             name VARCHAR(255) PRIMARY KEY,
#             quote TEXT NOT NULL,
#             advice TEXT NOT NULL
#         )
#     ''')
#     conn.commit()
#     close_db(conn, cur)


# def create_user_data(name, quote, advice):
#     conn, cur = create_cursor()
#     cur.execute("INSERT INTO user_details (name, quote, advice) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING",
#                 (name, quote, advice))
#     conn.commit()
#     close_db(conn, cur)


# # Initialize DB when app starts
# init_db()


# # --- Routes ---
# @app.route('/', methods=['POST', 'GET'])
# def input():
#     if request.method == 'POST':
#         name = request.form['username']
#         quote = request.form['quote']
#         advice = request.form['advice']
#         if name and quote and advice:
#             create_user_data(name, quote, advice)
#             return redirect(url_for('output'))
#         else:
#             return "⚠️ Please fill out all fields"
#     return render_template('index.html')


# @app.route('/output', methods=['GET'])
# def output():
#     conn, cur = create_cursor()
#     cur.execute("SELECT name, quote, advice FROM user_details;")
#     users = cur.fetchall()
#     close_db(conn, cur)
#     return render_template('response.html', users=users)


# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)


import os
import json
import boto3
import logging
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
import psycopg2
from psycopg2.extras import RealDictCursor

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")
csrf = CSRFProtect(app)

# --- DB Config (from env variables) ---
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_HOST = os.environ.get("DB_HOST", "python-db.cvyas68miksx.ap-south-1.rds.amazonaws.com")
DB_PORT = os.environ.get("DB_PORT", "5432")
SECRET_NAME = os.environ.get("SECRET_NAME", "rds!db-cfce6876-8455-42f4-8483-ab87766c6393")
REGION_NAME = os.environ.get("REGION_NAME", "ap-south-1")

# --- Secrets Manager Integration ---
_db_secret_cache = None

def get_db_secret():
    global _db_secret_cache
    if _db_secret_cache is None:
        try:
            client = boto3.client("secretsmanager", region_name=REGION_NAME)
            response = client.get_secret_value(SecretId=SECRET_NAME)
            _db_secret_cache = json.loads(response['SecretString'])
        except Exception as e:
            logging.error(f"Failed to retrieve secret: {e}")
            raise
    return _db_secret_cache


# --- Database Connection ---
def connect_db():
    secret = get_db_secret()
    try:
        conn = psycopg2.connect(
            database=DB_NAME,
            user=secret["username"],
            password=secret["password"],
            host=DB_HOST,
            port=DB_PORT,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logging.error(f"DB connection failed: {e}")
        raise


def init_db():
    """Initialize table with timestamp"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
       CREATE TABLE IF NOT EXISTS user_details (
            name VARCHAR(255) PRIMARY KEY,
            quote TEXT NOT NULL,
            advice TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()


# Initialize DB on startup
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
            conn = connect_db()
            cur = conn.cursor()
            # Upsert functionality: insert or update if exists
            cur.execute("""
                INSERT INTO user_details (name, quote, advice)
                VALUES (%s, %s, %s)
                ON CONFLICT (name)
                DO UPDATE SET quote = EXCLUDED.quote, advice = EXCLUDED.advice, created_at = CURRENT_TIMESTAMP
            """, (name, quote, advice))
            conn.commit()
            cur.close()
            conn.close()
            flash("Data saved successfully!", "success")
        except Exception as e:
            logging.error(f"Error saving user: {e}")
            flash("⚠️ Failed to save data. Try again.", "danger")
        return redirect(url_for('output'))
    return render_template('index.html', form=form)


@app.route('/output', methods=['GET'])
def output():
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT name, quote, advice, created_at FROM user_details ORDER BY created_at DESC;")
        users = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        users = []
        flash("⚠️ Could not fetch data.", "danger")
    return render_template('response.html', users=users)


@app.route('/delete/<string:name>', methods=['POST'])
def delete_user(name):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM user_details WHERE name=%s", (name,))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"User '{name}' deleted successfully!", "success")
    except Exception as e:
        logging.error(f"Error deleting user {name}: {e}")
        flash("⚠️ Could not delete user.", "danger")
    return redirect(url_for('output'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

