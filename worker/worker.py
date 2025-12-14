#!/usr/bin/env python3
"""
Chess Tournament Management System - Background Stats Worker

This worker runs on a Compute Engine VM and computes aggregated statistics
from the transactional database, writing results to the system_stats table.

Runs continuously with configurable interval between computations.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import mysql.connector
from mysql.connector import Error


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from MySQL."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('chess-worker')

# Configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'database': os.getenv('DB_NAME', 'chessdb')
}

# Worker settings
COMPUTE_INTERVAL = int(os.getenv('COMPUTE_INTERVAL', 300))  # 5 minutes default


def get_db_password():
    """Get DB password from Secret Manager if running on GCP."""
    gcp_project = os.getenv('GCP_PROJECT')
    if gcp_project:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{gcp_project}/secrets/chess-tournament-db-password/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.warning(f"Could not fetch secret from Secret Manager: {e}")
    return os.getenv('DB_PASSWORD', '1234')


def get_db_connection():
    """Create database connection."""
    try:
        config = DB_CONFIG.copy()
        config['password'] = get_db_password()
        connection = mysql.connector.connect(**config)
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None


def save_stat(cursor, conn, stat_name, stat_value, category='general'):
    """Save a statistic to the system_stats table."""
    try:
        # Delete old stat with same name
        cursor.execute(
            "DELETE FROM system_stats WHERE stat_name = %s",
            (stat_name,)
        )
        # Insert new stat
        cursor.execute(
            """INSERT INTO system_stats (stat_name, stat_value, stat_category)
               VALUES (%s, %s, %s)""",
            (stat_name, json.dumps(stat_value, cls=DecimalEncoder) if isinstance(stat_value, (dict, list)) else str(stat_value), category)
        )
        conn.commit()
        logger.debug(f"Saved stat: {stat_name} = {stat_value}")
    except Error as e:
        logger.error(f"Error saving stat {stat_name}: {e}")
        conn.rollback()


def compute_team_statistics(cursor, conn):
    """Compute team-level statistics."""
    logger.info("Computing team statistics...")

    # Total matches per team
    cursor.execute("""
        SELECT t.team_id, t.team_name,
               COUNT(DISTINCT m.match_id) as total_matches
        FROM teams t
        LEFT JOIN matches m ON t.team_id = m.team1_id OR t.team_id = m.team2_id
        GROUP BY t.team_id, t.team_name
        ORDER BY total_matches DESC
    """)
    matches_per_team = cursor.fetchall()
    save_stat(cursor, conn, 'matches_per_team', [
        {'team_id': r['team_id'], 'team_name': r['team_name'], 'matches': r['total_matches']}
        for r in matches_per_team
    ], 'teams')

    # Team win rates
    cursor.execute("""
        SELECT t.team_id, t.team_name,
               SUM(CASE
                   WHEN (m.team1_id = t.team_id AND ma.result = 'white wins')
                     OR (m.team2_id = t.team_id AND ma.result = 'black wins')
                   THEN 1 ELSE 0
               END) as wins,
               COUNT(ma.match_id) as total_games
        FROM teams t
        LEFT JOIN matches m ON t.team_id = m.team1_id OR t.team_id = m.team2_id
        LEFT JOIN match_assignments ma ON m.match_id = ma.match_id
        GROUP BY t.team_id, t.team_name
    """)
    team_win_rates = cursor.fetchall()
    save_stat(cursor, conn, 'team_win_rates', [
        {
            'team_id': r['team_id'],
            'team_name': r['team_name'],
            'wins': r['wins'] or 0,
            'total_games': r['total_games'] or 0,
            'win_rate': round((r['wins'] or 0) / max(r['total_games'] or 1, 1) * 100, 2)
        }
        for r in team_win_rates
    ], 'teams')


def compute_player_statistics(cursor, conn):
    """Compute player-level statistics."""
    logger.info("Computing player statistics...")

    # Top players by ELO
    cursor.execute("""
        SELECT username, name, surname, elorating, nationality
        FROM players
        ORDER BY elorating DESC
        LIMIT 10
    """)
    top_players = cursor.fetchall()
    save_stat(cursor, conn, 'top_players_by_elo', [
        {
            'username': r['username'],
            'name': f"{r['name']} {r['surname']}",
            'elo': r['elorating'],
            'nationality': r['nationality']
        }
        for r in top_players
    ], 'players')

    # Most active players
    cursor.execute("""
        SELECT p.username, p.name, p.surname,
               COUNT(ma.match_id) as total_matches
        FROM players p
        LEFT JOIN match_assignments ma ON p.username = ma.white_player OR p.username = ma.black_player
        GROUP BY p.username, p.name, p.surname
        ORDER BY total_matches DESC
        LIMIT 10
    """)
    active_players = cursor.fetchall()
    save_stat(cursor, conn, 'most_active_players', [
        {
            'username': r['username'],
            'name': f"{r['name']} {r['surname']}",
            'matches': r['total_matches'] or 0
        }
        for r in active_players
    ], 'players')

    # Average ELO by nationality
    cursor.execute("""
        SELECT nationality, AVG(elorating) as avg_elo, COUNT(*) as player_count
        FROM players
        GROUP BY nationality
        HAVING player_count >= 2
        ORDER BY avg_elo DESC
    """)
    elo_by_nationality = cursor.fetchall()
    save_stat(cursor, conn, 'avg_elo_by_nationality', [
        {
            'nationality': r['nationality'],
            'avg_elo': round(r['avg_elo'], 0),
            'player_count': r['player_count']
        }
        for r in elo_by_nationality
    ], 'players')


def compute_match_statistics(cursor, conn):
    """Compute match-level statistics."""
    logger.info("Computing match statistics...")

    # Total matches
    cursor.execute("SELECT COUNT(*) as total FROM matches")
    total_matches = cursor.fetchone()['total']
    save_stat(cursor, conn, 'total_matches', total_matches, 'matches')

    # Matches by result
    cursor.execute("""
        SELECT result, COUNT(*) as count
        FROM match_assignments
        GROUP BY result
    """)
    results = cursor.fetchall()
    save_stat(cursor, conn, 'matches_by_result', {
        r['result']: r['count'] for r in results
    }, 'matches')

    # Matches per month
    cursor.execute("""
        SELECT DATE_FORMAT(date, '%Y-%m') as month, COUNT(*) as count
        FROM matches
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    monthly = cursor.fetchall()
    save_stat(cursor, conn, 'matches_per_month', [
        {'month': r['month'], 'count': r['count']}
        for r in monthly
    ], 'matches')

    # Average rating by arbiter
    cursor.execute("""
        SELECT arbiter_username, AVG(ratings) as avg_rating, COUNT(*) as rated_count
        FROM matches
        WHERE ratings IS NOT NULL
        GROUP BY arbiter_username
    """)
    arbiter_ratings = cursor.fetchall()
    save_stat(cursor, conn, 'arbiter_avg_ratings', [
        {
            'arbiter': r['arbiter_username'],
            'avg_rating': round(r['avg_rating'], 2) if r['avg_rating'] else 0,
            'rated_count': r['rated_count']
        }
        for r in arbiter_ratings
    ], 'arbiters')


def compute_hall_statistics(cursor, conn):
    """Compute hall utilization statistics."""
    logger.info("Computing hall statistics...")

    # Matches per hall
    cursor.execute("""
        SELECT h.hall_id, h.hall_name, h.hall_country, h.hall_capacity,
               COUNT(m.match_id) as match_count
        FROM halls h
        LEFT JOIN matches m ON h.hall_id = m.hall_id
        GROUP BY h.hall_id, h.hall_name, h.hall_country, h.hall_capacity
        ORDER BY match_count DESC
    """)
    hall_usage = cursor.fetchall()
    save_stat(cursor, conn, 'hall_utilization', [
        {
            'hall_id': r['hall_id'],
            'hall_name': r['hall_name'],
            'country': r['hall_country'],
            'capacity': r['hall_capacity'],
            'matches_hosted': r['match_count'] or 0
        }
        for r in hall_usage
    ], 'halls')


def compute_summary_statistics(cursor, conn):
    """Compute overall summary statistics."""
    logger.info("Computing summary statistics...")

    stats = {}

    cursor.execute("SELECT COUNT(*) as count FROM users")
    stats['total_users'] = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM players")
    stats['total_players'] = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM coaches")
    stats['total_coaches'] = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM arbiters")
    stats['total_arbiters'] = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM teams")
    stats['total_teams'] = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM matches")
    stats['total_matches'] = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM halls")
    stats['total_halls'] = cursor.fetchone()['count']

    cursor.execute("SELECT AVG(elorating) as avg FROM players")
    result = cursor.fetchone()
    stats['average_player_elo'] = round(result['avg'], 0) if result['avg'] else 0

    save_stat(cursor, conn, 'summary', stats, 'summary')


def run_computations():
    """Run all statistical computations."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False

    try:
        cursor = conn.cursor(dictionary=True)

        compute_summary_statistics(cursor, conn)
        compute_team_statistics(cursor, conn)
        compute_player_statistics(cursor, conn)
        compute_match_statistics(cursor, conn)
        compute_hall_statistics(cursor, conn)

        # Save last computation time
        save_stat(cursor, conn, 'last_computed_at', datetime.now().isoformat(), 'meta')

        logger.info("All computations completed successfully")
        return True

    except Error as e:
        logger.error(f"Error during computations: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def main():
    """Main worker loop."""
    logger.info("Chess Tournament Stats Worker starting...")
    logger.info(f"Compute interval: {COMPUTE_INTERVAL} seconds")
    logger.info(f"Database host: {DB_CONFIG['host']}")

    while True:
        try:
            start_time = time.time()
            success = run_computations()

            elapsed = time.time() - start_time
            logger.info(f"Computation {'succeeded' if success else 'failed'} in {elapsed:.2f}s")

            # Sleep until next interval
            sleep_time = max(COMPUTE_INTERVAL - elapsed, 10)
            logger.info(f"Sleeping for {sleep_time:.0f} seconds...")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(60)  # Wait before retrying


if __name__ == '__main__':
    main()
