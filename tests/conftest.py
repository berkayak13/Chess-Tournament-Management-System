"""
Pytest configuration and fixtures for Chess Tournament Management System tests.
"""
import os
import pytest
import mysql.connector
from mysql.connector import Error

# Set testing environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['DB_NAME'] = 'chessdb_test'

from app import app, get_db_connection, User


@pytest.fixture(scope='session')
def test_db_config():
    """Database configuration for tests."""
    return {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '1234'),
    }


@pytest.fixture(scope='session')
def setup_test_database(test_db_config):
    """Create and setup test database once per test session."""
    # Connect without database to create it
    conn = mysql.connector.connect(**test_db_config)
    cursor = conn.cursor()

    # Create test database
    cursor.execute("DROP DATABASE IF EXISTS chessdb_test")
    cursor.execute("CREATE DATABASE chessdb_test")
    cursor.execute("USE chessdb_test")

    # Read and execute schema from triggers.sql
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'code', 'triggers.sql'
    )

    with open(schema_path, 'r') as f:
        sql_content = f.read()

    # Split by delimiter and execute each command
    commands = sql_content.split('$$')
    for command in commands:
        command = command.strip()
        if command and not command.startswith('DELIMITER'):
            try:
                cursor.execute(command)
                conn.commit()
            except Error as e:
                # Skip errors for DROP IF EXISTS, etc.
                if 'already exists' not in str(e).lower():
                    pass

    cursor.close()
    conn.close()

    yield

    # Cleanup after all tests
    conn = mysql.connector.connect(**test_db_config)
    cursor = conn.cursor()
    cursor.execute("DROP DATABASE IF EXISTS chessdb_test")
    cursor.close()
    conn.close()


@pytest.fixture(scope='function')
def test_db(setup_test_database, test_db_config):
    """Provide a database connection for each test."""
    config = {**test_db_config, 'database': 'chessdb_test'}
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)

    yield conn, cursor

    # Rollback any uncommitted changes
    conn.rollback()
    cursor.close()
    conn.close()


@pytest.fixture(scope='function')
def seed_test_data(test_db):
    """Seed basic test data for each test."""
    conn, cursor = test_db

    # Clear existing data (in correct order for foreign keys)
    tables = [
        'match_assignments', 'matches', 'player_teams', 'match_tables',
        'coach_certifications', 'coaches', 'teams', 'sponsors',
        'players', 'title', 'arbiter_certifications', 'arbiters',
        'managers', 'users', 'halls'
    ]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except Error:
            pass

    conn.commit()

    # Insert test users
    cursor.execute("""
        INSERT INTO users (username, password, role) VALUES
        ('test_manager', 'password123', 'manager'),
        ('test_player', 'password123', 'player'),
        ('test_coach', 'password123', 'coach'),
        ('test_arbiter', 'password123', 'arbiter')
    """)

    # Insert manager
    cursor.execute("""
        INSERT INTO managers (username, password) VALUES
        ('test_manager', 'password123')
    """)

    # Insert title (required for players)
    cursor.execute("""
        INSERT INTO title (title_id, title_name) VALUES
        (1, 'Grandmaster'),
        (2, 'International Master')
    """)

    # Insert sponsor (required for teams)
    cursor.execute("""
        INSERT INTO sponsors (sponsor_id, sponsor_name) VALUES
        (1, 'Test Sponsor')
    """)

    # Insert teams
    cursor.execute("""
        INSERT INTO teams (team_id, team_name, sponsor_id) VALUES
        (1, 'Test Team 1', 1),
        (2, 'Test Team 2', 1)
    """)

    # Insert halls
    cursor.execute("""
        INSERT INTO halls (hall_id, hall_name, hall_country, hall_capacity) VALUES
        (1, 'Test Hall', 'USA', 10)
    """)

    # Insert match tables
    cursor.execute("""
        INSERT INTO match_tables (table_id, hall_id) VALUES
        (1, 1),
        (2, 1)
    """)

    # Insert arbiter with certification
    cursor.execute("""
        INSERT INTO arbiters (username, password, name, surname, nationality, experience_level)
        VALUES ('test_arbiter', 'password123', 'Test', 'Arbiter', 'USA', 'advanced')
    """)
    cursor.execute("""
        INSERT INTO arbiter_certifications (username, certification)
        VALUES ('test_arbiter', 'FIDE Certified')
    """)

    # Insert player
    cursor.execute("""
        INSERT INTO players (username, password, name, surname, nationality,
                           dateofbirth, elorating, fideid, titleid, team_list)
        VALUES ('test_player', 'password123', 'Test', 'Player', 'USA',
                '2000-01-01', 2000, 'FIDE001', 1, '')
    """)

    # Add player to team
    cursor.execute("""
        INSERT INTO player_teams (username, team_id) VALUES
        ('test_player', 1)
    """)

    # Insert coach
    cursor.execute("""
        INSERT INTO coaches (username, password, name, surname, nationality,
                           team_id, contract_start, contract_finish)
        VALUES ('test_coach', 'password123', 'Test', 'Coach', 'USA',
                1, '2024-01-01', '2026-01-01')
    """)

    conn.commit()

    yield

    # Cleanup is handled by test_db fixture rollback


@pytest.fixture
def flask_app():
    """Create Flask application for testing."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(flask_app, setup_test_database, seed_test_data):
    """Create a test client for the Flask app."""
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    """Factory fixture to create logged-in test clients for different roles."""
    def _login(username, password='password123'):
        client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
        return client
    return _login


@pytest.fixture
def manager_client(logged_in_client):
    """Test client logged in as manager."""
    return logged_in_client('test_manager')


@pytest.fixture
def player_client(logged_in_client):
    """Test client logged in as player."""
    return logged_in_client('test_player')


@pytest.fixture
def coach_client(logged_in_client):
    """Test client logged in as coach."""
    return logged_in_client('test_coach')


@pytest.fixture
def arbiter_client(logged_in_client):
    """Test client logged in as arbiter."""
    return logged_in_client('test_arbiter')
