import boto3
import json
from flask import Flask, redirect, url_for, render_template, request
import psycopg2

app = Flask(__name__)

# Change these values to match your setup
SECRET_NAME = "mydb/credentials"   # The secret name in Secrets Manager
REGION_NAME = "us-east-1"          # AWS region where your secret is stored


# --- Secrets Manager Integration ---
_db_secret_cache = None  # simple cache

def get_db_secret():
    """Fetch DB credentials from AWS Secrets Manager"""
    global _db_secret_cache
    if _db_secret_cache is None:
        client = boto3.client("secretsmanager", region_name=REGION_NAME)
        response = client.get_secret_value(SecretId=SECRET_NAME)
        _db_secret_cache = json.loads(response['SecretString'])
    return _db_secret_cache


# --- Database Connection ---
def connect_db():
    secret = get_db_secret()
    conn = psycopg2.connect(
        database=secret["dbname"],
        user=secret["username"],
        password=secret["password"],
        host=secret["host"],
        port=secret["port"]
    )
    return conn


def create_cursor():
    conn = connect_db()
    cur = conn.cursor()
    return conn, cur


def close_db(conn, cur):
    cur.close()
    conn.close()


# --- Initialize Table ---
def init_db():
    conn, cur = create_cursor()
    cur.execute('''
       CREATE TABLE IF NOT EXISTS user_details (
            name VARCHAR(255) PRIMARY KEY,
            quote TEXT NOT NULL,
            advice TEXT NOT NULL
        )
    ''')
    conn.commit()
    close_db(conn, cur)


def create_user_data(name, quote, advice):
    conn, cur = create_cursor()
    cur.execute("INSERT INTO user_details (name, quote, advice) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING",
                (name, quote, advice))
    conn.commit()
    close_db(conn, cur)


# Initialize DB when app starts
init_db()


# --- Routes ---
@app.route('/', methods=['POST', 'GET'])
def input():
    if request.method == 'POST':
        name = request.form['username']
        quote = request.form['quote']
        advice = request.form['advice']
        if name and quote and advice:
            create_user_data(name, quote, advice)
            return redirect(url_for('output'))
        else:
            return "⚠️ Please fill out all fields"
    return render_template('index.html')


@app.route('/output', methods=['GET'])
def output():
    conn, cur = create_cursor()
    cur.execute("SELECT name, quote, advice FROM user_details;")
    users = cur.fetchall()
    close_db(conn, cur)
    return render_template('response.html', users=users)


if __name__ == '__main__':
    # run on port 80 for EC2 / container deployment
    app.run(debug=True, host='0.0.0.0', port=80)
