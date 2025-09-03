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
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request, flash, jsonify
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, validators
from wtforms.validators import DataRequired, Length
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import os
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-in-production')
    DB_NAME = "postgres"
    DB_HOST = "python-db.cvyas68miksx.ap-south-1.rds.amazonaws.com"
    DB_PORT = "5432"
    SECRET_NAME = "rds!db-cfce6876-8455-42f4-8483-ab87766c6393"
    REGION_NAME = "ap-south-1"
    MAX_CONNECTIONS = 20
    MIN_CONNECTIONS = 1

app = Flask(__name__)
app.config.from_object(Config)

# Enable CSRF protection
csrf = CSRFProtect(app)

# Global variables
db_secret_cache = None
connection_pool = None

# --- Forms ---
class UserForm(FlaskForm):
    username = StringField('Name', [
        DataRequired(message="Name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    quote = TextAreaField('Quote', [
        DataRequired(message="Quote is required"),
        Length(min=5, max=500, message="Quote must be between 5 and 500 characters")
    ])
    advice = TextAreaField('Advice', [
        DataRequired(message="Advice is required"),
        Length(min=5, max=1000, message="Advice must be between 5 and 1000 characters")
    ])

# --- Decorators ---
def handle_db_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except psycopg2.Error as e:
            logger.error(f"Database error in {f.__name__}: {str(e)}")
            flash("Database error occurred. Please try again.", "error")
            return redirect(url_for('input'))
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            flash("An unexpected error occurred. Please try again.", "error")
            return redirect(url_for('input'))
    return decorated_function

def rate_limit(max_requests=10, window=60):
    """Simple in-memory rate limiting"""
    requests = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            now = time.time()
            
            # Clean old entries
            requests[client_ip] = [req_time for req_time in requests.get(client_ip, []) 
                                 if now - req_time < window]
            
            if len(requests.get(client_ip, [])) >= max_requests:
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            requests.setdefault(client_ip, []).append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Secrets Manager Integration ---
def get_db_secret():
    """Fetch DB credentials from AWS Secrets Manager with error handling"""
    global db_secret_cache
    if db_secret_cache is None:
        try:
            client = boto3.client("secretsmanager", region_name=Config.REGION_NAME)
            response = client.get_secret_value(SecretId=Config.SECRET_NAME)
            db_secret_cache = json.loads(response['SecretString'])
            logger.info("Successfully retrieved database credentials from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to retrieve secret from AWS Secrets Manager: {str(e)}")
            raise
    return db_secret_cache

# --- Database Connection Pool ---
def init_connection_pool():
    """Initialize database connection pool"""
    global connection_pool
    if connection_pool is None:
        try:
            secret = get_db_secret()
            connection_pool = ThreadedConnectionPool(
                Config.MIN_CONNECTIONS,
                Config.MAX_CONNECTIONS,
                database=Config.DB_NAME,
                user=secret["username"],
                password=secret["password"],
                host=Config.DB_HOST,
                port=Config.DB_PORT
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {str(e)}")
            raise

def get_db_connection():
    """Get connection from pool"""
    if connection_pool is None:
        init_connection_pool()
    return connection_pool.getconn()

def return_db_connection(conn):
    """Return connection to pool"""
    if connection_pool and conn:
        connection_pool.putconn(conn)

# --- Database Operations ---
def init_db():
    """Initialize database with improved schema"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_details (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    quote TEXT NOT NULL,
                    advice TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name)
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_details_name ON user_details(name);
                CREATE INDEX IF NOT EXISTS idx_user_details_created_at ON user_details(created_at);
            ''')
            conn.commit()
            logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    finally:
        if conn:
            return_db_connection(conn)

@handle_db_errors
def create_user_data(name, quote, advice):
    """Create or update user data"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO user_details (name, quote, advice) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (name) 
                DO UPDATE SET 
                    quote = EXCLUDED.quote,
                    advice = EXCLUDED.advice,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (name, quote, advice))
            result = cur.fetchone()
            conn.commit()
            logger.info(f"User data created/updated for: {name}")
            return result[0] if result else None
    finally:
        if conn:
            return_db_connection(conn)

@handle_db_errors
def get_all_users(limit=100, offset=0, search_term=None):
    """Get all users with pagination and search"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if search_term:
                cur.execute('''
                    SELECT id, name, quote, advice, created_at, updated_at
                    FROM user_details 
                    WHERE name ILIKE %s OR quote ILIKE %s OR advice ILIKE %s
                    ORDER BY updated_at DESC 
                    LIMIT %s OFFSET %s
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', limit, offset))
            else:
                cur.execute('''
                    SELECT id, name, quote, advice, created_at, updated_at
                    FROM user_details 
                    ORDER BY updated_at DESC 
                    LIMIT %s OFFSET %s
                ''', (limit, offset))
            
            users = cur.fetchall()
            
            # Get total count for pagination
            if search_term:
                cur.execute('''
                    SELECT COUNT(*) FROM user_details 
                    WHERE name ILIKE %s OR quote ILIKE %s OR advice ILIKE %s
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            else:
                cur.execute('SELECT COUNT(*) FROM user_details')
            
            total_count = cur.fetchone()['count']
            
            return users, total_count
    finally:
        if conn:
            return_db_connection(conn)

@handle_db_errors
def get_user_by_name(name):
    """Get specific user by name"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT id, name, quote, advice, created_at, updated_at
                FROM user_details 
                WHERE name = %s
            ''', (name,))
            return cur.fetchone()
    finally:
        if conn:
            return_db_connection(conn)

@handle_db_errors
def delete_user_by_name(name):
    """Delete user by name"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM user_details WHERE name = %s RETURNING id', (name,))
            result = cur.fetchone()
            conn.commit()
            return result is not None
    finally:
        if conn:
            return_db_connection(conn)

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
@rate_limit(max_requests=20, window=60)
def input():
    form = UserForm()
    
    if form.validate_on_submit():
        try:
            user_id = create_user_data(
                form.username.data.strip(),
                form.quote.data.strip(),
                form.advice.data.strip()
            )
            if user_id:
                flash(f"Successfully saved data for {form.username.data}!", "success")
                return redirect(url_for('output'))
            else:
                flash("Failed to save data. Please try again.", "error")
        except Exception as e:
            logger.error(f"Error saving user data: {str(e)}")
            flash("An error occurred while saving your data.", "error")
    
    return render_template('index.html', form=form)

@app.route('/output')
@app.route('/output/<int:page>')
def output(page=1):
    per_page = 10
    offset = (page - 1) * per_page
    search_term = request.args.get('search', '').strip()
    
    users, total_count = get_all_users(limit=per_page, offset=offset, search_term=search_term)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('response.html', 
                         users=users, 
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         search_term=search_term)

@app.route('/api/users', methods=['GET'])
def api_get_users():
    """API endpoint to get users as JSON"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        search_term = request.args.get('search', '').strip()
        
        offset = (page - 1) * per_page
        users, total_count = get_all_users(limit=per_page, offset=offset, search_term=search_term)
        
        return jsonify({
            'users': [dict(user) for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<name>', methods=['GET'])
def api_get_user(name):
    """API endpoint to get specific user"""
    user = get_user_by_name(name)
    if user:
        return jsonify(dict(user))
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/<name>', methods=['DELETE'])
@csrf.exempt  # For API endpoints, you might want to use different CSRF protection
def api_delete_user(name):
    """API endpoint to delete user"""
    if delete_user_by_name(name):
        return jsonify({'message': 'User deleted successfully'})
    return jsonify({'error': 'User not found'}), 404

@app.route('/user/<name>')
def user_profile(name):
    """Individual user profile page"""
    user = get_user_by_name(name)
    if not user:
        flash(f"User '{name}' not found.", "error")
        return redirect(url_for('output'))
    
    return render_template('user_profile.html', user=user)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        return_db_connection(conn)
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

# --- Application Lifecycle ---
@app.before_first_request
def initialize_app():
    """Initialize app on first request"""
    init_db()

@app.teardown_appcontext
def close_db_connections(error):
    """Clean up database connections"""
    pass  # Connection pool handles this automatically

if __name__ == '__main__':
    # Initialize database and connection pool
    try:
        init_db()
        logger.info("Application starting...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    finally:
        # Clean up connection pool on shutdown
        if connection_pool:
            connection_pool.closeall()
