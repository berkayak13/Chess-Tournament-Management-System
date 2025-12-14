"""
Chess Tournament Management System - Audit Logging Cloud Function

This HTTP Cloud Function receives audit events from the Flask application
and stores them in Cloud Storage and optionally in the database.

Events tracked:
- User login/logout
- Match creation
- Match rating submission
- User creation
"""

import os
import json
import functions_framework
from datetime import datetime
from google.cloud import storage
import mysql.connector
from mysql.connector import Error

# Configuration
AUDIT_BUCKET = os.getenv('AUDIT_BUCKET', 'chess-tournament-audit-logs')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME', 'chessdb')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Initialize Cloud Storage client
storage_client = storage.Client()


def get_db_connection():
    """Create database connection if configured."""
    if not all([DB_HOST, DB_USER, DB_PASSWORD]):
        return None
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def store_in_gcs(event_data):
    """Store audit event in Cloud Storage."""
    try:
        bucket = storage_client.bucket(AUDIT_BUCKET)

        # Create path: year/month/day/timestamp_event.json
        now = datetime.utcnow()
        path = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.isoformat()}_{event_data.get('event_type', 'unknown')}.json"

        blob = bucket.blob(path)
        blob.upload_from_string(
            json.dumps(event_data, indent=2),
            content_type='application/json'
        )

        print(f"Stored audit log: gs://{AUDIT_BUCKET}/{path}")
        return True

    except Exception as e:
        print(f"Error storing to GCS: {e}")
        return False


def store_in_db(event_data):
    """Store audit event in database (optional)."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Create audit_logs table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                username VARCHAR(50),
                details TEXT,
                ip_address VARCHAR(45),
                user_agent VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_event_type (event_type),
                INDEX idx_username (username),
                INDEX idx_created_at (created_at)
            )
        """)

        # Insert audit log
        cursor.execute("""
            INSERT INTO audit_logs (event_type, username, details, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            event_data.get('event_type'),
            event_data.get('username'),
            json.dumps(event_data.get('details', {})),
            event_data.get('ip_address'),
            event_data.get('user_agent')
        ))

        conn.commit()
        print(f"Stored audit log in database: {event_data.get('event_type')}")
        return True

    except Error as e:
        print(f"Error storing to database: {e}")
        return False

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@functions_framework.http
def audit_log(request):
    """
    HTTP Cloud Function for audit logging.

    Expected JSON payload:
    {
        "event_type": "login|logout|match_created|match_rated|user_created",
        "username": "user123",
        "details": {...},
        "ip_address": "1.2.3.4",
        "user_agent": "Mozilla/5.0..."
    }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for actual request
    headers = {'Access-Control-Allow-Origin': '*'}

    # Validate request
    if request.method != 'POST':
        return (json.dumps({'error': 'Method not allowed'}), 405, headers)

    try:
        request_json = request.get_json(silent=True)
    except Exception:
        request_json = None

    if not request_json:
        return (json.dumps({'error': 'Invalid JSON payload'}), 400, headers)

    # Validate required fields
    event_type = request_json.get('event_type')
    if not event_type:
        return (json.dumps({'error': 'event_type is required'}), 400, headers)

    # Add metadata
    event_data = {
        'event_type': event_type,
        'username': request_json.get('username'),
        'details': request_json.get('details', {}),
        'ip_address': request_json.get('ip_address') or request.remote_addr,
        'user_agent': request_json.get('user_agent') or request.headers.get('User-Agent'),
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'chess-tournament-app'
    }

    # Store in GCS (always)
    gcs_success = store_in_gcs(event_data)

    # Store in DB (optional)
    db_success = store_in_db(event_data)

    # Response
    result = {
        'status': 'success' if gcs_success else 'partial',
        'event_type': event_type,
        'timestamp': event_data['timestamp'],
        'stored_in_gcs': gcs_success,
        'stored_in_db': db_success
    }

    return (json.dumps(result), 200, headers)


# For local testing
if __name__ == '__main__':
    from flask import Flask, request as flask_request

    app = Flask(__name__)

    @app.route('/', methods=['POST', 'OPTIONS'])
    def test_handler():
        return audit_log(flask_request)

    app.run(debug=True, port=8080)
