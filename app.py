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
from forms import UserForm 

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")
csrf = CSRFProtect(app)

# --- DB Config (from env variables) ---
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_HOST = os.environ.get("DB_HOST", "myapp-dev-db.cvyas68miksx.ap-south-1.rds.amazonaws.com")
DB_PORT = os.environ.get("DB_PORT", "5432")
SECRET_NAME = os.environ.get("SECRET_NAME", "myapp-dev-db-secret")
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
        form = UserForm() 
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        users = []
        flash("⚠️ Could not fetch data.", "danger")
    return render_template('response.html', users=users, form=form)


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
    
# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint for ALB.
    Returns HTTP 200 OK if the app is running.
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

