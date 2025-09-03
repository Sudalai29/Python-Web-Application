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



import boto3
import json
import logging
from flask import Flask, redirect, url_for, render_template, request, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_NAME = "postgres"
DB_HOST = "python-db.cvyas68miksx.ap-south-1.rds.amazonaws.com"
DB_PORT = "5432"
SECRET_NAME = "rds!db-cfce6876-8455-42f4-8483-ab87766c6393"
REGION_NAME = "ap-south-1"

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')

# Cache for database secret
db_secret_cache = None

# --- Input Validation ---
def validate_input(name, quote, advice):
    """Basic input validation"""
    errors = []
    
    if not name or not name.strip():
        errors.append("Name is required")
    elif len(name.strip()) < 2 or len(name.strip()) > 100:
        errors.append("Name must be between 2 and 100 characters")
    
    if not quote or not quote.strip():
        errors.append("Quote is required")
    elif len(quote.strip()) < 5 or len(quote.strip()) > 500:
        errors.append("Quote must be between 5 and 500 characters")
    
    if not advice or not advice.strip():
        errors.append("Advice is required")
    elif len(advice.strip()) < 5 or len(advice.strip()) > 1000:
        errors.append("Advice must be between 5 and 1000 characters")
    
    return errors

# --- Secrets Manager Integration ---
def get_db_secret():
    """Fetch DB credentials from AWS Secrets Manager with error handling"""
    global db_secret_cache
    if db_secret_cache is None:
        try:
            client = boto3.client("secretsmanager", region_name=REGION_NAME)
            response = client.get_secret_value(SecretId=SECRET_NAME)
            db_secret_cache = json.loads(response['SecretString'])
            logger.info("Successfully retrieved database credentials")
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {str(e)}")
            raise
    return db_secret_cache

# --- Database Connection ---
def connect_db():
    try:
        secret = get_db_secret()
        conn = psycopg2.connect(
            database=DB_NAME,
            user=secret["username"],
            password=secret["password"],
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

def create_cursor():
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # Return dict-like results
    return conn, cur

def close_db(conn, cur):
    if cur:
        cur.close()
    if conn:
        conn.close()

# --- Initialize Table ---
def init_db():
    conn, cur = None, None
    try:
        conn, cur = create_cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_details (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                quote TEXT NOT NULL,
                advice TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        close_db(conn, cur)

def create_user_data(name, quote, advice):
    conn, cur = None, None
    try:
        conn, cur = create_cursor()
        # Use UPSERT to handle duplicates gracefully
        cur.execute('''
            INSERT INTO user_details (name, quote, advice) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (name) 
            DO UPDATE SET 
                quote = EXCLUDED.quote,
                advice = EXCLUDED.advice,
                created_at = CURRENT_TIMESTAMP
        ''', (name.strip(), quote.strip(), advice.strip()))
        conn.commit()
        logger.info(f"User data saved for: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save user data: {str(e)}")
        return False
    finally:
        close_db(conn, cur)

def get_all_users():
    conn, cur = None, None
    try:
        conn, cur = create_cursor()
        cur.execute("SELECT name, quote, advice, created_at FROM user_details ORDER BY created_at DESC")
        users = cur.fetchall()
        return users
    except Exception as e:
        logger.error(f"Failed to retrieve users: {str(e)}")
        return []
    finally:
        close_db(conn, cur)

# Initialize DB when app starts
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize app: {str(e)}")

# --- Routes ---
@app.route('/', methods=['POST', 'GET'])
def input():
    if request.method == 'POST':
        name = request.form.get('username', '')
        quote = request.form.get('quote', '')
        advice = request.form.get('advice', '')
        
        # Validate input
        errors = validate_input(name, quote, advice)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('index.html')
        
        # Save to database
        if create_user_data(name, quote, advice):
            flash(f"Successfully saved data for {name}!", 'success')
            return redirect(url_for('output'))
        else:
            flash("Failed to save data. Please try again.", 'error')
            return render_template('index.html')
    
    return render_template('index.html')

@app.route('/output', methods=['GET'])
def output():
    users = get_all_users()
    return render_template('response.html', users=users)

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    try:
        conn = connect_db()
        conn.close()
        return {"status": "healthy"}, 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}, 503

# --- Error Handlers ---
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    flash("An internal error occurred. Please try again.", 'error')
    return redirect(url_for('input'))

@app.errorhandler(404)
def not_found(error):
    flash("Page not found.", 'error')
    return redirect(url_for('input'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
