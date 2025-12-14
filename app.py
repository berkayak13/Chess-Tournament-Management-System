from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from config import get_config
from cache import init_cache, CacheHelper, CACHE_TIMEOUTS
import requests

# Load environment variables
load_dotenv()

# Get configuration based on environment
app_config = get_config()

app = Flask(__name__)
app.config['SECRET_KEY'] = app_config.SECRET_KEY
app.config['TESTING'] = getattr(app_config, 'TESTING', False)
app.config['WTF_CSRF_ENABLED'] = getattr(app_config, 'WTF_CSRF_ENABLED', True)

# Database configuration from config module
db_config = app_config.get_db_config()

# Initialize caching
cache = init_cache(app)
cache_helper = CacheHelper(cache)

# Cloud Function URL for audit logging
FUNCTION_URL = app_config.FUNCTION_URL

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'


def send_audit_log(event_type, username=None, details=None, request_obj=None):
    """Send audit log to Cloud Function (non-blocking)."""
    if not FUNCTION_URL:
        return

    try:
        payload = {
            'event_type': event_type,
            'username': username,
            'details': details or {},
            'ip_address': request_obj.remote_addr if request_obj else None,
            'user_agent': request_obj.headers.get('User-Agent') if request_obj else None
        }
        # Use a short timeout to not block the main request
        requests.post(FUNCTION_URL, json=payload, timeout=1)
    except Exception as e:
        app.logger.warning(f"Failed to send audit log: {e}")

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

class User(UserMixin):
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(username):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user_data:
                return User(user_data['username'], user_data['password'], user_data['role'])
        except Error as e:
            print(f"Error loading user: {e}")
    return None

# Player routes
@app.route('/player/dashboard')
@login_required
def player_dashboard():
    if current_user.role != 'player':
        flash('Access denied. Only players can access this page.')
        return redirect(url_for('index'))
    return render_template('player/dashboard.html')

@app.route('/player/matches')
@login_required
def player_matches():
    if current_user.role != 'player':
        flash('Access denied. Only players can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get all matches where the player participated
            query = """
                SELECT m.*, ma.*, 
                       t1.team_name as team1_name, 
                       t2.team_name as team2_name,
                       h.hall_name,
                       TIME_FORMAT(m.time_slot, '%H:%i') as formatted_time
                FROM match_assignments ma
                JOIN matches m ON ma.match_id = m.match_id
                JOIN teams t1 ON m.team1_id = t1.team_id
                JOIN teams t2 ON m.team2_id = t2.team_id
                JOIN halls h ON m.hall_id = h.hall_id
                WHERE ma.white_player = %s OR ma.black_player = %s
            """
            cursor.execute(query, (current_user.username, current_user.username))
            matches = cursor.fetchall()
            
            # Calculate statistics
            total_matches = len(matches)
            wins = sum(1 for m in matches if (
                (m['white_player'] == current_user.username and m['result'] == 'white wins') or
                (m['black_player'] == current_user.username and m['result'] == 'black wins')
            ))
            draws = sum(1 for m in matches if m['result'] == 'draw')
            losses = total_matches - wins - draws
            
            # Calculate win rate
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
            
            cursor.close()
            conn.close()
            
            return render_template('player/matches.html',
                                matches=matches,
                                total_matches=total_matches,
                                wins=wins,
                                draws=draws,
                                losses=losses,
                                win_rate=win_rate)
                                
        except Error as e:
            print(f"Error fetching matches: {e}")
            flash('Error fetching match data')
            return redirect(url_for('player_dashboard'))
    
    flash('Database connection error')
    return redirect(url_for('player_dashboard'))

@app.route('/player/statistics')
@login_required
def player_statistics():
    if current_user.role != 'player':
        flash('Access denied. Only players can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get player information
            cursor.execute("SELECT * FROM players WHERE username = %s", (current_user.username,))
            player = cursor.fetchone()
            
            # Get match history
            query = """
                SELECT m.*, ma.*, 
                       t1.team_name as team1_name, 
                       t2.team_name as team2_name,
                       h.hall_name
                FROM match_assignments ma
                JOIN matches m ON ma.match_id = m.match_id
                JOIN teams t1 ON m.team1_id = t1.team_id
                JOIN teams t2 ON m.team2_id = t2.team_id
                JOIN halls h ON m.hall_id = h.hall_id
                WHERE ma.white_player = %s OR ma.black_player = %s
                ORDER BY m.date DESC
            """
            cursor.execute(query, (current_user.username, current_user.username))
            matches = cursor.fetchall()
            
            # Calculate statistics
            total_matches = len(matches)
            wins = sum(1 for m in matches if (
                (m['white_player'] == current_user.username and m['result'] == 'white wins') or
                (m['black_player'] == current_user.username and m['result'] == 'black wins')
            ))
            draws = sum(1 for m in matches if m['result'] == 'draw')
            losses = total_matches - wins - draws
            
            # Calculate win rate
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
            
            # Calculate performance by color
            white_matches = [m for m in matches if m['white_player'] == current_user.username]
            black_matches = [m for m in matches if m['black_player'] == current_user.username]
            
            white_wins = sum(1 for m in white_matches if m['result'] == 'white wins')
            black_wins = sum(1 for m in black_matches if m['result'] == 'black wins')
            
            white_win_rate = (white_wins / len(white_matches) * 100) if white_matches else 0
            black_win_rate = (black_wins / len(black_matches) * 100) if black_matches else 0
            
            cursor.close()
            conn.close()
            
            return render_template('player/statistics.html',
                                player=player,
                                total_matches=total_matches,
                                wins=wins,
                                draws=draws,
                                losses=losses,
                                win_rate=win_rate,
                                white_matches=len(white_matches),
                                black_matches=len(black_matches),
                                white_wins=white_wins,
                                black_wins=black_wins,
                                white_win_rate=white_win_rate,
                                black_win_rate=black_win_rate)
                                
        except Error as e:
            print(f"Error fetching statistics: {e}")
            flash('Error fetching statistics')
            return redirect(url_for('player_dashboard'))
    
    flash('Database connection error')
    return redirect(url_for('player_dashboard'))

@app.route('/player/opponents')
@login_required
def player_opponents():
    if current_user.role != 'player':
        flash('Access denied. Only players can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('player_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Call the stored procedure to get opponent statistics
        # showCoPlayerStats returns two result sets: 1) list of opponents, 2) avg ELO of most frequent
        cursor.callproc('showCoPlayerStats', [current_user.username])
        
        # Fetch the first result set (the list of opponents)
        opponents = []
        most_frequent_opponent_elo = None
        
        # Iterate through the result sets
        results = []
        for result in cursor.stored_results():
            results.append(result.fetchall())
            
        if len(results) > 0:
            opponents = results[0] # First result set is the list of opponents
            
        if len(results) > 1 and results[1]:
             # Second result set contains the average ELO of the most frequent opponent(s)
             # The column name from the procedure is 'Most_Frequent_Opponent_ELO'
             most_frequent_opponent_elo_data = results[1][0]
             most_frequent_opponent_elo = most_frequent_opponent_elo_data.get('Most_Frequent_Opponent_ELO')
             
        cursor.close()
        conn.close()
        
        return render_template('player/opponents.html', 
                             opponents=opponents,
                             most_frequent_opponent_elo=most_frequent_opponent_elo)
        
    except Error as e:
        print(f"Error fetching player opponents: {str(e)}")
        flash(f'Error fetching opponents: {str(e)}')
        return redirect(url_for('player_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s",
                             (username, password))
                user_data = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if user_data:
                    user = User(user_data['username'], user_data['password'], user_data['role'])
                    login_user(user)
                    # Audit log for successful login
                    send_audit_log('login', username=username, details={'role': user_data['role']}, request_obj=request)
                    return redirect(url_for('index'))
                flash('Invalid username or password')
            except Error as e:
                print(f"Error during login: {e}")
                flash('Database error during login')
        else:
            flash('Database connection error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Audit log for logout
    send_audit_log('logout', username=current_user.id, request_obj=request)
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'manager':
            return redirect(url_for('manager_dashboard'))
        elif current_user.role == 'player':
            return redirect(url_for('player_dashboard'))
        elif current_user.role == 'coach':
            return redirect(url_for('coach_dashboard'))
        elif current_user.role == 'arbiter':
            return redirect(url_for('arbiter_dashboard'))
    return render_template('index.html')

# Manager routes
@app.route('/manager/dashboard')
@login_required
def manager_dashboard():
    if current_user.role != 'manager':
        flash('Access denied. Only managers can access this page.')
        return redirect(url_for('index'))
    return render_template('manager/dashboard.html')

@app.route('/manager/halls', methods=['GET', 'POST'])
@login_required
def manager_halls():
    if current_user.role != 'manager':
        flash('Access denied. Only managers can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('manager_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            hall_id = request.form.get('hall_id')
            new_name = request.form.get('hall_name')
            
            try:
                cursor.execute("UPDATE halls SET hall_name = %s WHERE hall_id = %s",
                             (new_name, hall_id))
                conn.commit()
                flash('Hall name updated successfully!')
            except Error as e:
                conn.rollback()
                flash(f'Error updating hall: {str(e)}')
        
        # Get all halls
        cursor.execute("SELECT * FROM halls")
        halls = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('manager/halls.html', halls=halls)
        
    except Error as e:
        print(f"Error in halls management: {e}")
        flash('Database error')
        return redirect(url_for('manager_dashboard'))

@app.route('/manager/create_user', methods=['GET', 'POST'])
@login_required
def manager_create_user():
    if current_user.role != 'manager':
        flash('Access denied. Only managers can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('manager_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            name = request.form.get('name')
            surname = request.form.get('surname')
            nationality = request.form.get('nationality')
            
            try:
                # Start transaction
                cursor.execute("START TRANSACTION")
                
                # Create base user
                cursor.execute("""
                    INSERT INTO users (username, password, role)
                    VALUES (%s, %s, %s)
                """, (username, password, role))
                
                # Create role-specific user
                if role == 'player':
                    dateofbirth = datetime.strptime(request.form.get('dateofbirth'), '%Y-%m-%d').date()
                    elorating = int(request.form.get('elorating'))
                    fideid = request.form.get('fideid')
                    titleid = int(request.form.get('titleid'))
                    team_list = request.form.get('team_list')
                    
                    cursor.execute("""
                        INSERT INTO players (username, password, name, surname, nationality, 
                                          dateofbirth, elorating, fideid, titleid, team_list)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (username, password, name, surname, nationality, 
                         dateofbirth, elorating, fideid, titleid, team_list))
                    
                elif role == 'coach':
                    team_id = int(request.form.get('team_id'))
                    contract_start = datetime.strptime(request.form.get('contract_start'), '%Y-%m-%d').date()
                    contract_finish = datetime.strptime(request.form.get('contract_finish'), '%Y-%m-%d').date()
                    
                    cursor.execute("""
                        INSERT INTO coaches (username, password, name, surname, nationality,
                                          team_id, contract_start, contract_finish)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (username, password, name, surname, nationality,
                         team_id, contract_start, contract_finish))
                    
                elif role == 'arbiter':
                    experience_level = request.form.get('experience_level')
                    
                    cursor.execute("""
                        INSERT INTO arbiters (username, password, name, surname, nationality,
                                           experience_level)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (username, password, name, surname, nationality,
                         experience_level))
                
                # Commit transaction
                conn.commit()
                flash('User created successfully!')
                return redirect(url_for('manager_dashboard'))
                
            except Error as e:
                conn.rollback()
                flash(f'Error creating user: {str(e)}')
        
        # GET request - show form
        cursor.execute("SELECT * FROM teams")
        teams = cursor.fetchall()
        
        cursor.execute("SELECT * FROM title")
        titles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('manager/create_user.html', teams=teams, titles=titles)
        
    except Error as e:
        print(f"Error in user creation: {e}")
        flash('Database error')
        return redirect(url_for('manager_dashboard'))

# Match management routes
@app.route('/matches')
@login_required
def matches():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all matches with team names and hall info
        query = """
            SELECT m.*, 
                   t1.team_name as team1_name, 
                   t2.team_name as team2_name,
                   h.hall_name,
                   mt.table_id,
                   TIME_FORMAT(m.time_slot, '%H:%i') as formatted_time
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN halls h ON m.hall_id = h.hall_id
            JOIN match_tables mt ON m.table_id = mt.table_id
        """
        cursor.execute(query)
        matches = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('matches.html', matches=matches)
        
    except Error as e:
        print(f"Error fetching matches: {e}")
        flash('Error fetching match data')
        return redirect(url_for('index'))

@app.route('/matches/create', methods=['GET', 'POST'])
@login_required
def create_match():
    if current_user.role not in ['admin']:
        flash('You do not have permission to create matches')
        return redirect(url_for('matches'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('matches'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            try:
                # Get form data
                date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
                time = datetime.strptime(request.form['time'], '%H:%M').time()
                hall_id = int(request.form['hall_id'])
                table_id = int(request.form['table_id'])
                team1_id = int(request.form['team1_id'])
                team2_id = int(request.form['team2_id'])
                arbiter_username = request.form['arbiter_username']
                
                # Validate teams are different
                if team1_id == team2_id:
                    flash('Teams must be different')
                    return redirect(url_for('create_match'))
                
                # Check hall/table availability
                cursor.execute("""
                    SELECT * FROM matches 
                    WHERE date = %s 
                    AND hall_id = %s 
                    AND table_id = %s 
                    AND (
                        (time_slot <= %s AND %s < ADDTIME(time_slot, '02:00:00'))
                        OR (%s <= time_slot AND time_slot < ADDTIME(%s, '02:00:00'))
                    )
                """, (date, hall_id, table_id, time, time, time, time))
                
                if cursor.fetchone():
                    flash('The selected hall/table is already booked for this time slot')
                    return redirect(url_for('create_match'))
                
                # Create new match
                cursor.execute("""
                    INSERT INTO matches (date, time_slot, hall_id, table_id, team1_id, team2_id, arbiter_username)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (date, time, hall_id, table_id, team1_id, team2_id, arbiter_username))
                
                conn.commit()
                flash('Match created successfully')
                return redirect(url_for('matches'))
                
            except Error as e:
                conn.rollback()
                flash(f'Error creating match: {str(e)}')
                return redirect(url_for('create_match'))
        
        # GET request - show form
        cursor.execute("SELECT * FROM halls")
        halls = cursor.fetchall()
        
        cursor.execute("SELECT * FROM teams")
        teams = cursor.fetchall()
        
        cursor.execute("SELECT username FROM users WHERE role = 'arbiter'")
        arbiters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('create_match.html', halls=halls, teams=teams, arbiters=arbiters)
        
    except Error as e:
        print(f"Error in match creation: {e}")
        flash('Database error')
        return redirect(url_for('matches'))

@app.route('/matches/<int:match_id>/assign', methods=['GET', 'POST'])
@login_required
def assign_players(match_id):
    if current_user.role not in ['admin']:
        flash('You do not have permission to assign players')
        return redirect(url_for('matches'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('matches'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get match details
        cursor.execute("""
            SELECT m.*, 
                   t1.team_id as team1_id, 
                   t2.team_id as team2_id,
                   t1.team_name as team1_name,
                   t2.team_name as team2_name,
                   h.hall_name,
                   mt.table_id,
                   TIME_FORMAT(m.time_slot, '%H:%i') as formatted_time
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN halls h ON m.hall_id = h.hall_id
            JOIN match_tables mt ON m.table_id = mt.table_id
            WHERE m.match_id = %s
        """, (match_id,))
        match = cursor.fetchone()
        
        if not match:
            flash('Match not found')
            return redirect(url_for('matches'))
        
        if request.method == 'POST':
            try:
                white_player = request.form['white_player']
                black_player = request.form['black_player']
                result = request.form['result']
                
                # Validate players belong to correct teams
                cursor.execute("""
                    SELECT * FROM player_teams 
                    WHERE username = %s AND team_id = %s
                """, (white_player, match['team1_id']))
                if not cursor.fetchone():
                    flash('White player must be from Team 1')
                    return redirect(url_for('assign_players', match_id=match_id))
                
                cursor.execute("""
                    SELECT * FROM player_teams 
                    WHERE username = %s AND team_id = %s
                """, (black_player, match['team2_id']))
                if not cursor.fetchone():
                    flash('Black player must be from Team 2')
                    return redirect(url_for('assign_players', match_id=match_id))
                
                # Check for player schedule conflicts
                cursor.execute("""
                    SELECT * FROM match_assignments ma
                    JOIN matches m ON ma.match_id = m.match_id
                    WHERE m.date = %s
                    AND (
                        ma.white_player IN (%s, %s)
                        OR ma.black_player IN (%s, %s)
                    )
                    AND (
                        (m.time_slot <= %s AND %s < ADDTIME(m.time_slot, '02:00:00'))
                        OR (%s <= m.time_slot AND m.time_slot < ADDTIME(%s, '02:00:00'))
                    )
                """, (match['date'], white_player, black_player, white_player, black_player,
                      match['time_slot'], match['time_slot'], match['time_slot'], match['time_slot']))
                
                if cursor.fetchone():
                    flash('One or both players are already assigned to a match at this time')
                    return redirect(url_for('assign_players', match_id=match_id))
                
                # Create assignment
                cursor.execute("""
                    INSERT INTO match_assignments (match_id, white_player, black_player, result)
                    VALUES (%s, %s, %s, %s)
                """, (match_id, white_player, black_player, result))
                
                conn.commit()
                flash('Players assigned successfully')
                return redirect(url_for('matches'))
                
            except Error as e:
                conn.rollback()
                flash(f'Error assigning players: {str(e)}')
                return redirect(url_for('assign_players', match_id=match_id))
        
        # GET request - show form
        cursor.execute("""
            SELECT p.* FROM players p
            JOIN player_teams pt ON p.username = pt.username
            WHERE pt.team_id = %s
        """, (match['team1_id'],))
        team1_players = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.* FROM players p
            JOIN player_teams pt ON p.username = pt.username
            WHERE pt.team_id = %s
        """, (match['team2_id'],))
        team2_players = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('assign_players.html', 
                             match_id=match_id,
                             match=match,
                             team1_players=team1_players,
                             team2_players=team2_players)
        
    except Error as e:
        print(f"Error in player assignment: {e}")
        flash('Database error')
        return redirect(url_for('matches'))

# Coach routes
@app.route('/coach/dashboard')
@login_required
def coach_dashboard():
    if current_user.role != 'coach':
        flash('Access denied. Only coaches can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get coach's team information
        cursor.execute("""
            SELECT c.*, t.team_name 
            FROM coaches c
            JOIN teams t ON c.team_id = t.team_id
            WHERE c.username = %s
        """, (current_user.username,))
        coach_info = cursor.fetchone()
        
        if not coach_info:
            flash('Coach information not found')
            return redirect(url_for('index'))
        
        # Get recent matches for the coach's team
        cursor.execute("""
            SELECT m.*, 
                   t1.team_name as team1_name, 
                   t2.team_name as team2_name,
                   h.hall_name,
                   mt.table_id,
                   ma.result,
                   TIME_FORMAT(m.time_slot, '%H:%i') as formatted_time,
                   CASE 
                       WHEN m.team1_id = %s THEN t2.team_name
                       ELSE t1.team_name
                   END as opponent_team
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN halls h ON m.hall_id = h.hall_id
            JOIN match_tables mt ON m.table_id = mt.table_id
            LEFT JOIN match_assignments ma ON m.match_id = ma.match_id
            WHERE m.team1_id = %s OR m.team2_id = %s
            ORDER BY m.date DESC, m.time_slot DESC
            LIMIT 10
        """, (coach_info['team_id'], coach_info['team_id'], coach_info['team_id']))
        recent_matches = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('coach/dashboard.html', 
                             coach=coach_info,
                             recent_matches=recent_matches)
        
    except Error as e:
        print(f"Error in coach dashboard: {e}")
        flash('Database error')
        return redirect(url_for('index'))

@app.route('/coach/matches/create', methods=['GET', 'POST'])
@login_required
def coach_create_match():
    if current_user.role != 'coach':
        flash('Access denied. Only coaches can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('coach_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get coach's team information
        cursor.execute("""
            SELECT c.*, t.team_name 
            FROM coaches c
            JOIN teams t ON c.team_id = t.team_id
            WHERE c.username = %s
        """, (current_user.username,))
        coach_info = cursor.fetchone()
        
        if not coach_info:
            flash('Coach information not found')
            return redirect(url_for('coach_dashboard'))
        
        if request.method == 'POST':
            try:
                # Get form data
                date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
                time_slot_int = int(request.form['time_slot']) # Get integer time slot
                hall_id = int(request.form['hall_id'])
                table_id = int(request.form['table_id'])
                team2_id = int(request.form['team2_id'])
                arbiter_username = request.form['arbiter_username']
                
                # Map time slot integer to actual time
                time_slot_map = {
                    1: '01:00:00',
                    2: '02:00:00',
                    3: '03:00:00'
                }
                
                if time_slot_int not in time_slot_map:
                     flash('Invalid time slot selected')
                     return redirect(url_for('coach_create_match'))
                     
                start_time = time_slot_map[time_slot_int]

                # Validate teams are different
                if team2_id == coach_info['team_id']:
                    flash('Cannot create match against your own team')
                    return redirect(url_for('coach_create_match'))
                
                # Validate time slot
                if time_slot_int not in [1, 2, 3]:
                    flash('Time slot must be 1, 2, or 3')
                    return redirect(url_for('coach_create_match'))
                
                # Check hall/table availability for both time slots (using the calculated start_time and duration)
                cursor.execute("""
                    SELECT * FROM matches 
                    WHERE date = %s 
                    AND hall_id = %s 
                    AND table_id = %s 
                    AND (
                        (time_slot <= %s AND %s < ADDTIME(time_slot, '02:00:00'))
                        OR (%s <= time_slot AND time_slot < ADDTIME(%s, '02:00:00'))
                    )
                """, (date, hall_id, table_id, start_time, start_time, start_time, start_time))
                
                if cursor.fetchone():
                    flash('The selected hall/table is already booked for these time slots')
                    return redirect(url_for('coach_create_match'))
                
                # Get the next available match_id
                cursor.execute("SELECT COALESCE(MAX(match_id), 0) + 1 as next_id FROM matches")
                next_match_id = cursor.fetchone()['next_id']
                
                # Create new match
                cursor.execute("""
                    INSERT INTO matches (match_id, date, time_slot, hall_id, table_id, team1_id, team2_id, arbiter_username)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (next_match_id, date, start_time, hall_id, table_id, coach_info['team_id'], team2_id, arbiter_username))
                
                conn.commit()
                flash('Match created successfully')
                # Audit log for match creation
                send_audit_log('match_created', username=current_user.id,
                             details={'match_id': next_match_id, 'team1_id': coach_info['team_id'],
                                     'team2_id': team2_id, 'date': str(date)}, request_obj=request)
                return redirect(url_for('coach_dashboard'))

            except Error as e:
                conn.rollback()
                flash(f'Error creating match: {str(e)}')
                return redirect(url_for('coach_create_match'))
        
        # GET request - show form
        cursor.execute("""
            SELECT h.*, COUNT(mt.table_id) as num_tables
            FROM halls h
            LEFT JOIN match_tables mt ON h.hall_id = mt.hall_id
            GROUP BY h.hall_id
        """)
        halls = cursor.fetchall()
        
        cursor.execute("""
            SELECT t.* FROM teams t
            WHERE t.team_id != %s
        """, (coach_info['team_id'],))
        teams = cursor.fetchall()
        
        cursor.execute("SELECT username FROM users WHERE role = 'arbiter'")
        arbiters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('coach/create_match.html', 
                             halls=halls, 
                             teams=teams, 
                             arbiters=arbiters,
                             coach=coach_info)
        
    except Error as e:
        print(f"Error in match creation: {e}")
        flash('Database error')
        return redirect(url_for('coach_dashboard'))

@app.route('/coach/matches/<int:match_id>/assign', methods=['GET', 'POST'])
@login_required
def coach_assign_players(match_id):
    if current_user.role != 'coach':
        flash('Access denied. Only coaches can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('coach_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get coach's team information
        cursor.execute("""
            SELECT c.*, t.team_name 
            FROM coaches c
            JOIN teams t ON c.team_id = t.team_id
            WHERE c.username = %s
        """, (current_user.username,))
        coach_info = cursor.fetchone()
        
        if not coach_info:
            flash('Coach information not found')
            return redirect(url_for('coach_dashboard'))
        
        # Get match details
        cursor.execute("""
            SELECT m.*, 
                   t1.team_id as team1_id, 
                   t2.team_id as team2_id,
                   t1.team_name as team1_name,
                   t2.team_name as team2_name,
                   h.hall_name,
                   mt.table_id,
                   TIME_FORMAT(m.time_slot, '%H:%i') as formatted_time
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN halls h ON m.hall_id = h.hall_id
            JOIN match_tables mt ON m.table_id = mt.table_id
            WHERE m.match_id = %s
        """, (match_id,))
        match = cursor.fetchone()
        
        if not match:
            flash('Match not found')
            return redirect(url_for('coach_dashboard'))
        
        # Verify coach's team is involved in the match
        if match['team1_id'] != coach_info['team_id'] and match['team2_id'] != coach_info['team_id']:
            flash('You can only assign players for matches involving your team')
            return redirect(url_for('coach_dashboard'))
        
        if request.method == 'POST':
            try:
                white_player = request.form['white_player']
                black_player = request.form['black_player']
                result = request.form['result']
                
                # Determine which team the coach is assigning for
                is_team1 = match['team1_id'] == coach_info['team_id']
                coach_player = white_player if is_team1 else black_player
                opponent_player = black_player if is_team1 else white_player
                
                # Validate players belong to correct teams
                cursor.execute("""
                    SELECT * FROM player_teams 
                    WHERE username = %s AND team_id = %s
                """, (coach_player, coach_info['team_id']))
                if not cursor.fetchone():
                    flash('Selected player must be from your team')
                    return redirect(url_for('coach_assign_players', match_id=match_id))
                
                cursor.execute("""
                    SELECT * FROM player_teams 
                    WHERE username = %s AND team_id = %s
                """, (opponent_player, match['team2_id'] if is_team1 else match['team1_id']))
                if not cursor.fetchone():
                    flash('Opponent player must be from the other team')
                    return redirect(url_for('coach_assign_players', match_id=match_id))
                
                # Check for player schedule conflicts
                cursor.execute("""
                    SELECT * FROM match_assignments ma
                    JOIN matches m ON ma.match_id = m.match_id
                    WHERE m.date = %s
                    AND (
                        ma.white_player IN (%s, %s)
                        OR ma.black_player IN (%s, %s)
                    )
                    AND (
                        (m.time_slot <= %s AND %s < ADDTIME(m.time_slot, '02:00:00'))
                        OR (%s <= m.time_slot AND m.time_slot < ADDTIME(%s, '02:00:00'))
                    )
                """, (match['date'], white_player, black_player, white_player, black_player,
                      match['time_slot'], match['time_slot'], match['time_slot'], match['time_slot']))
                
                if cursor.fetchone():
                    flash('One or both players are already assigned to a match at this time')
                    return redirect(url_for('coach_assign_players', match_id=match_id))
                
                # Create assignment
                cursor.execute("""
                    INSERT INTO match_assignments (match_id, white_player, black_player, result)
                    VALUES (%s, %s, %s, %s)
                """, (match_id, white_player, black_player, result))
                
                conn.commit()
                flash('Players assigned successfully')
                return redirect(url_for('coach_dashboard'))
                
            except Error as e:
                conn.rollback()
                print(f"Error assigning players: {str(e)}")
                flash(f'Error assigning players: {str(e)}')
                return redirect(url_for('coach_assign_players', match_id=match_id))
        
        # GET request - show form
        cursor.execute("""
            SELECT p.* FROM players p
            JOIN player_teams pt ON p.username = pt.username
            WHERE pt.team_id = %s
        """, (coach_info['team_id'],))
        team_players = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.* FROM players p
            JOIN player_teams pt ON p.username = pt.username
            WHERE pt.team_id = %s
        """, (match['team2_id'] if match['team1_id'] == coach_info['team_id'] else match['team1_id'],))
        opponent_players = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('coach/assign_players.html', 
                             match_id=match_id,
                             match=match,
                             team_players=team_players,
                             opponent_players=opponent_players,
                             coach=coach_info)
        
    except Error as e:
        print(f"Error in player assignment: {str(e)}")
        flash(f'Database error: {str(e)}')
        return redirect(url_for('coach_dashboard'))

@app.route('/coach/matches/<int:match_id>/delete', methods=['POST'])
@login_required
def coach_delete_match(match_id):
    if current_user.role != 'coach':
        flash('Access denied. Only coaches can delete matches.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('coach_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get coach's team information
        cursor.execute("""
            SELECT c.team_id
            FROM coaches c
            WHERE c.username = %s
        """, (current_user.username,))
        coach_team = cursor.fetchone()
        
        if not coach_team:
            flash('Coach information not found.')
            return redirect(url_for('coach_dashboard'))
            
        coach_team_id = coach_team['team_id']
        
        # Verify that the match exists and was created by the coach's team
        cursor.execute("""
            SELECT match_id FROM matches
            WHERE match_id = %s AND (team1_id = %s OR team2_id = %s)
        """, (match_id, coach_team_id, coach_team_id))
        match_to_delete = cursor.fetchone()
        
        if not match_to_delete:
            flash('Match not found or you do not have permission to delete it.')
            return redirect(url_for('coach_dashboard'))
            
        # Call the stored procedure to delete the match
        cursor.callproc('deleteMatch', [match_id])
        
        conn.commit()
        flash('Match deleted successfully.')
        
    except Error as e:
        conn.rollback()
        print(f"Error deleting match: {str(e)}")
        flash(f'Error deleting match: {str(e)}')
        
    finally:
        if conn:
            cursor.close()
            conn.close()
            
    return redirect(url_for('coach_dashboard'))

@app.route('/coach/halls')
@login_required
def coach_view_halls():
    if current_user.role != 'coach':
        flash('Access denied. Only coaches can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('coach_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Call the stored procedure to view halls
        cursor.callproc('viewHalls')
        
        # Fetch the result set
        # Note: callproc returns multiple result sets if the procedure executes multiple SELECTs
        # We expect only one result set from viewHalls
        for result in cursor.stored_results():
            halls = result.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('coach/halls.html', halls=halls)
        
    except Error as e:
        print(f"Error viewing halls: {str(e)}")
        flash(f'Error viewing halls: {str(e)}')
        return redirect(url_for('coach_dashboard'))

# Arbiter routes
@app.route('/arbiter/dashboard')
@login_required
def arbiter_dashboard():
    if current_user.role != 'arbiter':
        flash('Access denied. Only arbiters can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get matches assigned to this arbiter
        cursor.execute("""
            SELECT m.*, 
                   t1.team_name as team1_name, 
                   t2.team_name as team2_name,
                   h.hall_name,
                   mt.table_id,
                   ma.result,
                   TIME_FORMAT(m.time_slot, '%H:%i') as formatted_time,
                   CASE 
                       WHEN ma.result IS NOT NULL THEN 'Completed'
                       ELSE 'Pending'
                   END as status
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN halls h ON m.hall_id = h.hall_id
            JOIN match_tables mt ON m.table_id = mt.table_id
            LEFT JOIN match_assignments ma ON m.match_id = ma.match_id
            WHERE m.arbiter_username = %s
            ORDER BY m.date DESC, m.time_slot DESC
        """, (current_user.username,))
        matches = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('arbiter/dashboard.html', matches=matches)
        
    except Error as e:
        print(f"Error in arbiter dashboard: {e}")
        flash('Database error')
        return redirect(url_for('index'))

@app.route('/arbiter/matches/<int:match_id>/rate', methods=['GET', 'POST'])
@login_required
def arbiter_rate_match(match_id):
    if current_user.role != 'arbiter':
        flash('Access denied. Only arbiters can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('arbiter_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get match details
        cursor.execute("""
            SELECT m.*, 
                   t1.team_name as team1_name, 
                   t2.team_name as team2_name,
                   h.hall_name,
                   mt.table_id,
                   ma.result,
                   ma.white_player,
                   ma.black_player,
                   TIME_FORMAT(m.time_slot, '%H:%i') as formatted_time,
                   COALESCE(m.ratings, '') as ratings
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN halls h ON m.hall_id = h.hall_id
            JOIN match_tables mt ON m.table_id = mt.table_id
            LEFT JOIN match_assignments ma ON m.match_id = ma.match_id
            WHERE m.match_id = %s AND m.arbiter_username = %s
        """, (match_id, current_user.username))
        match = cursor.fetchone()
        
        if not match:
            flash('Match not found or you are not assigned as the arbiter')
            return redirect(url_for('arbiter_dashboard'))
        
        # Check if the match date has passed
        if match['date'] >= datetime.now().date():
            flash('Cannot rate a match whose date has not yet passed.')
            return redirect(url_for('arbiter_dashboard'))
        
        if match['ratings']:
            flash('This match has already been rated')
            return redirect(url_for('arbiter_dashboard'))
        
        if request.method == 'POST':
            try:
                rating = int(request.form['rating'])
                
                # Validate rating
                if not (1 <= rating <= 10):
                    flash('Rating must be between 1 and 10')
                    return redirect(url_for('arbiter_rate_match', match_id=match_id))
                
                # Update match with rating
                cursor.execute("""
                    UPDATE matches 
                    SET ratings = %s
                    WHERE match_id = %s
                """, (str(rating), match_id))
                
                conn.commit()
                flash('Match rated successfully')
                # Audit log for match rating
                send_audit_log('match_rated', username=current_user.id,
                             details={'match_id': match_id, 'rating': rating}, request_obj=request)
                return redirect(url_for('arbiter_dashboard'))

            except Error as e:
                conn.rollback()
                print(f"Error rating match: {str(e)}")
                flash(f'Error rating match: {str(e)}')
                return redirect(url_for('arbiter_rate_match', match_id=match_id))
        
        cursor.close()
        conn.close()
        
        return render_template('arbiter/rate_match.html', match=match)
        
    except Error as e:
        print(f"Error in match rating: {str(e)}")
        flash(f'Database error: {str(e)}')
        return redirect(url_for('arbiter_dashboard'))

@app.route('/arbiter/statistics')
@login_required
def arbiter_statistics():
    if current_user.role != 'arbiter':
        flash('Access denied. Only arbiters can access this page.')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('arbiter_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Call the stored procedure to show match statistics for the current arbiter
        cursor.callproc('showMatchStats', [current_user.username])
        
        # Fetch the result set
        # We expect one result set with total_matches_rated and avg_rating
        stats = None
        for result in cursor.stored_results():
            stats = result.fetchone()
        
        cursor.close()
        conn.close()
        
        if not stats:
            # Handle case where the arbiter hasn't rated any matches yet
            stats = {'Total_Matches_Rated': 0, 'Avg_Rating': 0.0}
            
        return render_template('arbiter/statistics.html', stats=stats)
        
    except Error as e:
        print(f"Error fetching arbiter statistics: {str(e)}")
        flash(f'Error fetching statistics: {str(e)}')
        return redirect(url_for('arbiter_dashboard'))

@app.route('/api/halls/<int:hall_id>/tables')
@login_required
@cache_helper.cached(timeout=CACHE_TIMEOUTS['api_tables'], key_prefix='hall_tables')
def get_hall_tables(hall_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get tables for the specified hall
        cursor.execute("""
            SELECT table_id 
            FROM match_tables 
            WHERE hall_id = %s
        """, (hall_id,))
        tables = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(tables)
        
    except Error as e:
        print(f"Error fetching tables: {e}")
        return jsonify({'error': 'Database error'}), 500


# Admin Stats Route (displays worker-computed statistics)
@app.route('/admin/stats')
@login_required
def admin_stats():
    if current_user.role != 'manager':
        flash('Access denied. Only managers can access this page.')
        return redirect(url_for('index'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('manager_dashboard'))

    try:
        cursor = conn.cursor(dictionary=True)

        # Get all system stats computed by the worker
        cursor.execute("""
            SELECT stat_name, stat_value, stat_category, computed_at
            FROM system_stats
            ORDER BY stat_category, stat_name
        """)
        raw_stats = cursor.fetchall()

        # Parse JSON values and organize by category
        stats = {}
        for row in raw_stats:
            category = row['stat_category']
            if category not in stats:
                stats[category] = {}

            try:
                import json
                value = json.loads(row['stat_value'])
            except (json.JSONDecodeError, TypeError):
                value = row['stat_value']

            stats[category][row['stat_name']] = {
                'value': value,
                'computed_at': row['computed_at']
            }

        cursor.close()
        conn.close()

        return render_template('admin/stats.html', stats=stats)

    except Error as e:
        print(f"Error fetching admin stats: {str(e)}")
        flash(f'Error fetching statistics: {str(e)}')
        return redirect(url_for('manager_dashboard'))


if __name__ == '__main__':
    app.run(debug=True) 